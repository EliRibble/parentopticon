import collections
import datetime
import logging
import sqlite3
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from parentopticon.db.connection import Connection
from parentopticon.db.tables import Process, Program, ProgramProcess, ProgramSession, WindowWeek, WindowWeekDay

LOGGER = logging.getLogger(__name__)

StatementAndBinding = Tuple[str, Iterable[Any]]

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

def program_session_create_or_add(connection: Connection, elapsed_seconds: int, program_name: str, pids: Iterable[int]) -> int:
	"Either create a new program session or update an existing one."
	program = Program.search(connection, name=program_name)
	program_session = ProgramSession.search(connection, program=program.id, end=None)
	if program_session is None:
		return ProgramSession.insert(connection,
			end = None,
			pids = ",".join(sorted(pids)),
			program = program.id,
			start = datetime.datetime.now(),
		)
	return program_session.id
			
			
		

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
			

def program_session_list_open(connection: Connection) -> Iterable[ProgramSession]:
	"""Get all the open program sessions."""
	for data in connection.cursor.execute(
		"SELECT id, end, start, program FROM ProgramSession WHERE end IS NULL",
		):
		yield ProgramSession(
			id_ = data[0],
			end = data[1],
			start = data[2],
			program_id = data[3],
		)

def program_session_list_since(connection: Connection, moment: datetime.datetime) -> Iterable[ProgramSession]:
	"""Get all program sessions that started after a moment."""
	for data in connection.cursor.execute(
		"SELECT id, end, start, program FROM ProgramSession WHERE start > ?",
		(moment,)):
		yield ProgramSession(
			id_ = data[0],
			end = data[1],
			start = data[2],
			program_id = data[3],
		)

def snapshot_store(connection: Connection, elapsed_seconds: int, pid_to_program: Mapping[int, str]) -> None:
	"Take a snapshot from a host, store it."
	# create a list of pids for each program
	program_to_pids = collections.defaultdict(list)
	for pid, program in pid_to_program.items():
		program_to_pids[program].append(pid)
	for program, pids in program_to_pids.items():
		program_session_create_or_add(connection, elapsed_seconds, program, pids)
	

def window_week_day_span_create(connection: Connection, day: int, end: int, start: int, window_id: int) -> int:
	connection.execute(
		"INSERT INTO WindowWeekDaySpan (day, end, start, window_id) VALUES (?, ?, ?, ?)",
		(day, end, start, window_id))
	connection.commit()
	return connection.lastrowid

