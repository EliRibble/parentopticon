import collections
import datetime
import logging
import sqlite3
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from parentopticon.db.connection import Connection
from parentopticon.db.tables import OneTimeMessage, Process, Program, ProgramGroup, ProgramProcess, ProgramSession, WindowWeek, WindowWeekDay

LOGGER = logging.getLogger(__name__)

StatementAndBinding = Tuple[str, Iterable[Any]]

Action = collections.namedtuple("Action", (
	"content",
	"type",
))
def actions_for_username(connection: Connection, hostname: str, username: str) -> Iterable[Action]:
	LOGGER.info("Getting list of actions for %s on '%s'", username, hostname)
	messages = actions_for_username_messages(connection, hostname, username)
	kills = actions_for_username_kills(connection, hostname, username)
	return messages + kills

def actions_for_username_messages(connection: Connection, hostname: str, username: str) -> Iterable[Action]:
	one_time_messages = list(OneTimeMessage.list(
		connection,
		username=username,
		sent=None,
	))
	LOGGER.info("Got %d one-time messages for %s", len(one_time_messages), username)
	for otm in one_time_messages:
		OneTimeMessage.update(
			connection,
			otm.id,
			hostname=hostname,
			sent=datetime.datetime.now(),
		)
	return [Action(
		content=otm.content,
		type="warn",
	) for otm in one_time_messages]

def actions_for_username_kills(connection: Connection, hostname: str, username: str) -> Iterable[Action]:
	program_groups = list(ProgramGroup.list(connection))
	programs = list(Program.list(connection))
	statuses = _user_to_status_for(connection, username, program_groups, programs)
	pids = set()
	for status in statuses.values():
		if status.minutes_remaining_today < 0:
			pids.update(status.pids)
	LOGGER.info("Killing pids %s", pids)
	return []
	return [Action(
		content = pid,
		type = "kill",
	) for pid in pids]

def list_program_by_process(connection: Connection) -> Mapping[str, str]:
	"Get the mapping of processes to their program names."
	programs = Program.list(connection)
	program_by_id = {program.id: program.name for program in programs}
	processes = ProgramProcess.list(connection)
	return {process.name: program_by_id[process.program] for process in processes}

def program_session_close(connection: Connection, program_session_id: int) -> None:
	connection.execute(
		"UPDATE ProgramSession SET end = ? WHERE id = ?",
		(datetime.datetime.now(), program_session_id)
	)

def program_session_create_or_add(
		connection: Connection,
		hostname: str,
		username: str,
		elapsed_seconds: int,
		program_name: str, pids: Iterable[int]) -> int:
	"Either create a new program session or update an existing one."
	program = Program.search(connection, name=program_name)
	program_session = ProgramSession.search(connection,
		program=program.id,
		hostname=hostname,
		username=username,
		end=None)
	if program_session is None:
		program_session_id = ProgramSession.insert(connection,
			end = None,
			hostname = hostname,
			pids = ",".join(sorted(pids)),
			program = program.id,
			start = datetime.datetime.now(),
			username = username,
		)
		LOGGER.debug("Created new program session %s", program_session_id)
	else:
		program_session_id = program_session.id
		ProgramSession.update(connection,
			program_session_id,
			pids = ",".join(sorted(pids)),
		)
		LOGGER.debug("Updated program session %d to have pids %s",
			program_session_id,
			sorted(pids))
	return program_session_id
			
			
		

def program_session_ensure_closed(connection: Connection, program_id: int) -> None:
	"""Make sure any open program sessions are now closed."""
	program_session = program_session_get_open(program_id)
	if not program_session:
		return
	program_session_close(program_session.id)

def program_session_ensure_exists(connection: Connection, program_name: str, pids: int) -> int:
	"""Make sure an open program session exists for the program."""
	program_session = program_session_get_open(connection, program_id)
	if program_session:
		return program_session.id_
	return program_session_create(
		connection,
		end = None,
		start = datetime.datetime.now(),
		program_id=program_id)


def program_session_list_by_program(connection: Connection, program_id: int) -> Iterable[ProgramSession]:
	"""Get all the program sessions for a particular program."""
	for data in connection.cursor.execute(
		"SELECT id, end, start, program FROM ProgramSession WHERE program == ? ORDER BY start",
		(program_id,)):
		yield ProgramSession(
			id_ = data[0],
			end = data[1],
			start = data[2],
			program_id = data[3],
		)
			

def program_session_list_since(
		connection: Connection,
		moment: datetime.datetime,
		programs: Optional[List[int]]) -> Iterable[ProgramSession]:
	"""Get all program sessions that started after a moment."""
	if programs is None:
		where = "start > ?"
		bindings = (moment,)
	else:
		where = "start > ? AND program IN ({})".format(",".join(["?"]*len(programs)))
		bindings = [moment] + programs
	return ProgramSession.list_where(
		connection,
		where=where,
		bindings=bindings,
	)

def snapshot_store(
		connection: Connection,
		hostname: str,
		username: str,
		elapsed_seconds: int,
		pid_to_program: Mapping[int, str]) -> None:
	"Take a snapshot from a host, store it."
	# create a list of pids for each program
	program_to_pids = collections.defaultdict(list)
	for pid, program in pid_to_program.items():
		program_to_pids[program].append(pid)
	LOGGER.debug("Program to pids: %s", program_to_pids)
	for program, pids in program_to_pids.items():
		program_session_create_or_add(connection, hostname, username, elapsed_seconds, program, pids)
	

Status = collections.namedtuple("Status", (
	"group",
	"minutes_used_today",
	"minutes_remaining_today",
	"pids",
))
def user_to_status(connection: Connection) -> Mapping[str, Mapping[str, Status]]:
	"""Get a mapping of usernames to their current status.

	The results map from a username to another mapping. That inner mapping maps
	from a group name to the minutes left.
	"""
	results = {}
	program_groups = list(ProgramGroup.list(connection))
	programs = list(Program.list(connection))
	now = datetime.datetime.now()
	for username in usernames(connection):
		results[username] = _user_to_status_for(connection, username, program_groups, programs)
	return results

def usernames(connection: Connection) -> Iterable[str]:
	rows = connection.execute("SELECT DISTINCT username FROM ProgramSession").fetchall()
	usernames = [row[0] for row in rows]
	return usernames
	
def _minutes_allowed_today(program_group: ProgramGroup) -> int:
	"Get the minutes allowed today."
	today = datetime.datetime.now().isoweekday()
	prop = [
		"minutes_monday",
		"minutes_tuesday",
		"minutes_wednesday",
		"minutes_thursday",
		"minutes_friday",
		"minutes_saturday",
		"minutes_sunday",
	][today - 1]
	return getattr(program_group, prop)

def _today_start() -> datetime.datetime:
	"Get the starting moment for today."
	now = datetime.datetime.now()
	return now.replace(
		hour = 0,
		minute = 0,
		second = 0,
	)

def _user_to_status_for(connection: Connection,
		username: str, 
		program_groups: Iterable[ProgramGroup],
		programs: Iterable[Program],
		) -> Mapping[str, Status]:
	"""Get the mapping of group names to status for a given user."""
	results = {}
	now = datetime.datetime.now()
	for program_group in program_groups:
		programs_for_group = [program for program in programs if program.program_group == program_group.id]
		program_ids = [program.id for program in programs_for_group]
		program_sessions_today = program_session_list_since(connection, _today_start(), programs=program_ids)
		minutes_used_today = 0
		minutes_allowed_today = _minutes_allowed_today(program_group)
		pids = set()
		for program_session in program_sessions_today:
			end = program_session.end or now
			elapsed = (end - program_session.start)
			minutes_used_today += elapsed.total_seconds() / 60
			pids.add(program_session.pids)
		minutes_used_today = round(minutes_used_today, 1)
		results[program_group.name] = Status(
			group = program_group.id,
			minutes_used_today = minutes_used_today,
			minutes_remaining_today = minutes_allowed_today - minutes_used_today,
			pids = sorted(list(pids)),
		)
	return results

