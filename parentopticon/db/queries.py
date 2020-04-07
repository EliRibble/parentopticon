import collections
import datetime
import logging
import sqlite3
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from parentopticon.db.connection import Connection
from parentopticon.db.tables import Process, ProgramSession, WindowWeek, WindowWeekDay

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

def program_session_create(connection: Connection, end: Optional[datetime.date], start: datetime.datetime, program_id: int) -> int:
	connection.execute(
		"INSERT INTO ProgramSession (end, start, program) VALUES (?, ?, ?)",
		(end, start, program_id),
	)
	connection.commit()
	return connection.cursor.lastrowid

def program_session_ensure_closed(connection: Connection, program_id: int) -> None:
	"""Make sure any open program sessions are now closed."""
	program_session = program_session_get_open(program_id)
	if not program_session:
		return
	program_session_close(program_session.id)

def program_session_ensure_exists(connection: Connection, program_id: int) -> int:
	"""Make sure an open program session exists for the program."""
	program_session = program_session_get_open(connection, program_id)
	if program_session:
		return program_session.id_
	return program_session_create(
		connection,
		end = None,
		start = datetime.datetime.now(),
		program_id=program_id)


def program_session_get_open(connection: Connection, program_id: int) -> Optional[ProgramSession]:
	"""Get a program session, if it exists."""
	connection.execute(
		"SELECT id, end, start, program FROM ProgramSession WHERE program == ? AND end IS NULL",
		(program_id,)
	)
	data = connection.cursor.fetchone()
	if not data:
		return
	return ProgramSession(
		id_ = data[0],
		end = data[1],
		start = data[2],
		program_id = data[3],
	)

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

def process_create(connection: Connection, name: str, program: int) -> int:
	connection.cursor.execute(
		"INSERT INTO ProgramProcess (name, program) VALUES (?, ?)",
		(name, program),
	)
	connection.commit()
	return connection.cursor.lastrowid
	
def program_process_list(connection: Connection, program_id: int) -> Iterable[Process]:
	for data in connection.execute(
		"SELECT id, name, program FROM ProgramProcess WHERE program == ?",
		(program_id,),
	):
		yield Process(
			id = data[0],
			name = data[1],
			program_id = data[2],
		)

def window_week_create(connection: Connection, name: str) -> int:
	connection.execute(
		"INSERT INTO WindowWeek (name) VALUES (?)",
		(name,))
	connection.commit()
	return connection.cursor.lastrowid

def window_week_get(connection: Connection, window_id: int) -> WindowWeek:
	days = window_week_day_list(window_id)
	connection.execute(
		"SELECT id, name FROM WindowWeek WHERE id = ?", (window_id,))
	data = connection.cursor.fetchone()
	return WindowWeek(
		id_ = data[0],
		name = data[1],
		days = days,
	)

def window_week_list(connection: Connection) -> Iterable[WindowWeek]:
	for data in connection.cursor.execute(
		"SELECT id, name FROM WindowWeek"):
		days = window_week_day_list(data[0])
		yield WindowWeek(
			id_ = data[0],
			name = data[1],
			days = days,
		)
	
def window_week_day_span_create(connection: Connection, day: int, end: int, start: int, window_id: int) -> int:
	connection.execute(
		"INSERT INTO WindowWeekDaySpan (day, end, start, window_id) VALUES (?, ?, ?, ?)",
		(day, end, start, window_id))
	connection.commit()
	return connection.lastrowid

def window_week_day_get(connection: Connection, window_id: int, day: int) -> WindowWeekDay:
	spans = [WindowWeekDaySpan(
		id_ = data[0],
		day = data[1],
		end = data[2],
		start = data[3],
		window_id = data[4],
	) for data in connection.execute(
		"SELECT id, day, end, start, window_id FROM WindowWeekDaySpan WHERE window_id = ? AND day = ?",
		(window_id, day),
	)]
	return WindowWeekDay(
		day = day,
		spans = spans,
		window_id = window_id,
	)

def window_week_day_list(connection: Connection, window_id: int) -> List[WindowWeekDay]:
	spans = [WindowWeekDaySpan(
		id_ = data[0],
		day = data[1],
		end = data[2],
		start = data[3],
		window_id = data[4],
	) for data in connection.execute(
		"SELECT id, day, end, start, window_id FROM WindowWeekDaySpan WHERE window_id = ?",
		(window_id,),
	)]
	results = [WindowWeekDay(
		day = i,
		spans = [],
		window_id = window_id,
	) for i in range(7)]
	for span in spans:
		results[span.day].spans.append(span)
	return results

