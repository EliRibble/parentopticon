import collections
import datetime
import logging
import sqlite3
from typing import Iterable, List, Optional

LOGGER = logging.getLogger(__name__)

Group = collections.namedtuple("Group", ("id", "name", "limit", "window_week"))
Limit = collections.namedtuple("Limit", ("id", "name", "daily", "weekly", "monthly"))
Process = collections.namedtuple("Process", ("id", "name", "program_id"))
Program = collections.namedtuple("Program", ("id", "name", "group", "processes"))

class ProgramSession:
	def __init__(self, id_: int, end: datetime.datetime, start: datetime.datetime, program_id: int) -> None:
		self.id = id_
		self.end = end
		self.start = start
		self.program_id = program_id

	@property
	def duration(self) -> Optional[datetime.timedelta]:
		"Get the duration of the session, if possible."
		if self.start and self.end:
			return self.end - self.start

class WindowWeekDaySpan:
	def __init__(self, id_: int, day: int, end: int, start: int, window_id: int):
		self.id = id_
		self.day = day
		self.end = end
		self.start = start
		self.window_id = window_id

	def minutes_left(self, moment: datetime.time) -> int:
		"""Get the minutes left in the span for a moment.

		Returns: 0 if the current moment falls outside of the span,
			or the number of minutes left until the span ends if the
			current moment is inside the span.
		"""
		
		return max(span.minutes_left(moment) for span in self.spans)

	@property
	def value(self) -> str:
		return "{}-{}".format(self.start, self.end)

class WindowWeekDay:
	def __init__(self, window_id: int, day: int, spans: List[WindowWeekDaySpan]):
		self.window_id = window_id
		self.day = day
		self.spans = sorted(spans, key=lambda s: s.start)

	def minutes_left(self, moment: datetime.time) -> int:
		"""Get the minutes left in the window week day for a moment.

		Returns: 0 if the current moment falls outside of a span,
			or the number of minutes left until the span ends if the
			current moment is inside a window.
		"""
		return max(span.minutes_left(moment) for span in self.spans)

	@property
	def value(self) -> str:
		return ",".join(span.value for span in self.spans)

class WindowWeek:
	def __init__(self, id_: int, name: str, days: List[WindowWeekDay]):
		self.id = id_
		self.name = name
		self.days = days

	def from_iso_weekday(self, day: int) -> WindowWeekDay:
		"Get the correct day span from an isoweekday"
		return self.days[day-1]

	def minutes_left(self, moment: datetime.datetime) -> int:
		"""Get the minutes left in the window week for a given moment.

		Returns: 0 if the moment falls outside of a window,
			or the number of minutes left until the window ends if the
			current moment is inside a window.
		"""
		day = self.from_iso_weekday(moment.isoweekday())
		return day.minutes_left(moment.time())

	def today(self) -> WindowWeekDay:
		"Get the day span for today."
		return self.from_iso_weekday(datetime.datetime.now().isoweekday())

	@property
	def monday(self) -> WindowWeekDay:
		return self.days[0]

	@property
	def tuesday(self) -> WindowWeekDay:
		return self.days[1]

	@property
	def wednesday(self) -> WindowWeekDay:
		return self.days[2]

	@property
	def thursday(self) -> WindowWeekDay:
		return self.days[3]

	@property
	def friday(self) -> WindowWeekDay:
		return self.days[4]

	@property
	def saturday(self) -> WindowWeekDay:
		return self.days[5]

	@property
	def sunday(self) -> WindowWeekDay:
		return self.days[6]

class Connection:
	"Class that encapsulates all the interface to the DB."
	def __init__(self):
		self.connection = None
		self.cursor = None

	def connect(self, path: Optional[str] = "/usr/share/parentopticon/db.sqlite"):
		self.connection = sqlite3.connect(
			path,
			detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
		)
		self.cursor = self.connection.cursor()
		self._create_tables()

	def group_create(self, name: str, limit: Optional[int] = None, window_week: Optional[int] = None) -> int:
		self.cursor.execute(
			"INSERT INTO ProgramGroup (name, group_limit, window_week) VALUES (?, ?, ?)",
			(name, limit, window_week))
		self.connection.commit()
		return self.cursor.lastrowid

	def group_get(self, group_id: int) -> Group:
		self.cursor.execute(
			"SELECT id, name, group_limit, window_week FROM ProgramGroup WHERE id = ?", (group_id,))
		data = self.cursor.fetchone()
		limit = self.limit_get(data[2]) if data[2] else None
		window_week = self.window_week_get(data[3]) if data[3] else None
		return Group(
			id = data[0],
			name = data[1],
			limit = limit,
			window_week = window_week,
		)

	def group_list(self) -> Iterable[Group]:
		for data in self.cursor.execute(
			"SELECT id, name, group_limit, window_week FROM ProgramGroup"):
			limit = self.limit_get(data[2]) if data[2] else None
			window_week = self.window_week_get(data[3]) if data[3] else None
			yield Group(
				id = data[0],
				name = data[1],
				limit = limit,
				window_week = window_week,
			)
				
	def limit_create(self, name: str, daily: int, weekly: int, monthly: int) -> int:
		self.cursor.execute(
			"INSERT INTO ProgramGroupLimit (name, daily, weekly, monthly) VALUES (?, ?, ?, ?)",
			(name, daily, weekly, monthly))
		self.connection.commit()
		return self.cursor.lastrowid

	def limit_get(self, limit_id: int) -> Limit:
		self.cursor.execute(
			"SELECT id, name, daily, weekly, monthly FROM ProgramGroupLimit WHERE id = ?", (limit_id,))
		data = self.cursor.fetchone()
		return Limit(
			id = data[0],
			name = data[1],
			daily = data[2],
			weekly = data[3],
			monthly = data[4],
		)

	def limit_list(self) -> Iterable[Limit]:
		for data in self.cursor.execute(
			"SELECT id, name, daily, weekly, monthly FROM ProgramGroupLimit"):
			yield Limit(
				id = data[0],
				name = data[1],
				daily = data[2],
				weekly = data[3],
				monthly = data[4],
			)

	def program_create(self, name: str, group: int) -> int:
		self.cursor.execute(
			"INSERT INTO Program (name, program_group) VALUES (?, ?)",
			(name, group),
		)
		self.connection.commit()
		return self.cursor.lastrowid
		
	def program_get(self, program_id: int) -> Program:
		self.cursor.execute("SELECT id, name, program_group FROM Program")
		data = self.cursor.fetchone()
		group = self.group_get(data[2])
		processes = list(self.program_process_list(program_id))
		return Program(
			id = data[0],
			name = data[1],
			group = group,
			processes = processes,
		)
		
	def program_list(self) -> Iterable[Program]:
		for data in self.cursor.execute(
			"SELECT id, name, program_group FROM Program"):
			group = self.group_get(data[2])
			processes = list(self.program_process_list(data[0]))
			yield Program(
				id = data[0],
				name = data[1],
				group = group,
				processes = processes,
			)

	def program_session_close(self, program_session_id: int) -> None:
		self.cursor.execute(
			"UPDATE ProgramSession SET end = ? WHERE id = ?",
			(datetime.datetime.now(), program_session_id)
		)

	def program_session_create(self, end: Optional[datetime.date], start: datetime.datetime, program_id: int) -> int:
		self.cursor.execute(
			"INSERT INTO ProgramSession (end, start, program) VALUES (?, ?, ?)",
			(end, start, program_id),
		)
		self.connection.commit()
		return self.cursor.lastrowid

	def program_session_ensure_closed(self, program_id: int) -> None:
		"""Make sure any open program sessions are now closed."""
		program_session = self.program_session_get_open(program_id)
		if not program_session:
			return
		self.program_session_close(program_session.id)

	def program_session_ensure_exists(self, program_id: int) -> int:
		"""Make sure an open program session exists for the program."""
		program_session = self.program_session_get_open(program_id)
		if program_session:
			return program_session.id
		return self.program_session_create(
			end = None,
			start = datetime.datetime.now(),
			program_id=program_id)


	def program_session_get(self, program_id: int) -> Optional[ProgramSession]:
		"""Get a program session."""
		self.cursor.execute(
			"SELECT id, end, start, program FROM ProgramSession WHERE program == ?",
			(program_id,)
		)
		data = self.cursor.fetchone()
		return ProgramSession(
			id_ = data[0],
			end = data[1],
			start = data[2],
			program_id = data[3],
		)

	def program_session_get_open(self, program_id: int) -> Optional[ProgramSession]:
		"""Get a program session, if it exists."""
		self.cursor.execute(
			"SELECT id, end, start, program FROM ProgramSession WHERE program == ? AND end IS NULL",
			(program_id,)
		)
		data = self.cursor.fetchone()
		if not data:
			return
		return ProgramSession(
			id_ = data[0],
			end = data[1],
			start = data[2],
			program_id = data[3],
		)

	def program_session_list_by_program(self, program_id: int) -> Iterable[ProgramSession]:
		"""Get all the program sessions for a particular program."""
		for data in self.cursor.execute(
			"SELECT id, end, start, program FROM ProgramSession WHERE program == ? ORDER BY start",
			(program_id,)):
			yield ProgramSession(
				id_ = data[0],
				end = data[1],
				start = data[2],
				program_id = data[3],
			)
				

	def program_session_list_open(self) -> Iterable[ProgramSession]:
		"""Get all the open program sessions."""
		for data in self.cursor.execute(
			"SELECT id, end, start, program FROM ProgramSession WHERE end IS NULL",
			):
			yield ProgramSession(
				id_ = data[0],
				end = data[1],
				start = data[2],
				program_id = data[3],
			)

	def program_session_list_since(self, moment: datetime.datetime) -> Iterable[ProgramSession]:
		"""Get all program sessions that started after a moment."""
		for data in self.cursor.execute(
			"SELECT id, end, start, program FROM ProgramSession WHERE start > ?",
			(moment,)):
			yield ProgramSession(
				id_ = data[0],
				end = data[1],
				start = data[2],
				program_id = data[3],
			)

	def process_create(self, name: str, program: int) -> int:
		self.cursor.execute(
			"INSERT INTO ProgramProcess (name, program) VALUES (?, ?)",
			(name, program),
		)
		self.connection.commit()
		return self.cursor.lastrowid
		
	def program_process_list(self, program_id: int) -> Iterable[Process]:
		for data in self.cursor.execute(
			"SELECT id, name, program FROM ProgramProcess WHERE program == ?",
			(program_id,),
		):
			yield Process(
				id = data[0],
				name = data[1],
				program_id = data[2],
			)

	def truncate_all(self) -> None:
		self.cursor.execute(
			"DELETE FROM Program")
		self.cursor.execute(
			"DELETE FROM ProgramProcess")
		self.cursor.execute(
			"DELETE FROM ProgramGroupLimit")
		self.cursor.execute(
			"DELETE FROM ProgramGroup")
		self.cursor.execute(
			"DELETE FROM ProgramSession")
		self.cursor.execute(
			"DELETE FROM ProgramGroupLimitBonus")
		self.cursor.execute(
			"DELETE FROM UserSession")
		self.cursor.execute(
			"DELETE FROM WindowWeek")
		self.cursor.execute(
			"DELETE FROM WindowWeekDaySpan")
		self.cursor.execute(
			"DELETE FROM WindowWeekDayOverride ")

	def window_week_create(self, name: str) -> int:
		self.cursor.execute(
			"INSERT INTO WindowWeek (name) VALUES (?)",
			(name,))
		self.connection.commit()
		return self.cursor.lastrowid

	def window_week_get(self, window_id: int) -> WindowWeek:
		days = self.window_week_day_list(window_id)
		self.cursor.execute(
			"SELECT id, name FROM WindowWeek WHERE id = ?", (window_id,))
		data = self.cursor.fetchone()
		return WindowWeek(
			id_ = data[0],
			name = data[1],
			days = days,
		)

	def window_week_list(self) -> Iterable[WindowWeek]:
		for data in self.cursor.execute(
			"SELECT id, name FROM WindowWeek"):
			days = self.window_week_day_list(data[0])
			yield WindowWeek(
				id_ = data[0],
				name = data[1],
				days = days,
			)
		
	def window_week_day_span_create(self, day: int, end: int, start: int, window_id: int) -> int:
		self.cursor.execute(
			"INSERT INTO WindowWeekDaySpan (day, end, start, window_id) VALUES (?, ?, ?, ?)",
			(day, end, start, window_id))
		self.connection.commit()
		return self.cursor.lastrowid

	def window_week_day_get(self, window_id: int, day: int) -> WindowWeekDay:
		spans = [WindowWeekDaySpan(
			id_ = data[0],
			day = data[1],
			end = data[2],
			start = data[3],
			window_id = data[4],
		) for data in self.cursor.execute(
			"SELECT id, day, end, start, window_id FROM WindowWeekDaySpan WHERE window_id = ? AND day = ?",
			(window_id, day),
		)]
		return WindowWeekDay(
			day = day,
			spans = spans,
			window_id = window_id,
		)

	def window_week_day_list(self, window_id: int) -> List[WindowWeekDay]:
		spans = [WindowWeekDaySpan(
			id_ = data[0],
			day = data[1],
			end = data[2],
			start = data[3],
			window_id = data[4],
		) for data in self.cursor.execute(
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

	def _create_tables(self):
		LOGGER.info("Ensuring DB tables exist.")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS Program (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				program_group INTEGER NOT NULL -- ProgramGroup FK
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramProcess (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				program INTEGER NOT NULL -- Program FK
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramGroupLimit (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				daily INTEGER NOT NULL,
				weekly INTEGER NOT NULL,
				monthly INTEGER NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramGroup (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				group_limit INTEGER, -- Limit FK
				window_week INTEGER -- WindowWeek FK
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS UserSession (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				end timestamp,
				start timestamp NOT NULL,
				username TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramSession (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				end timestamp,
				start timestamp NOT NULL,
				program INTEGER NOT NULL -- Program FK
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramGroupLimitBonus (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				amount INTEGER NOT NULL,
				created timestamp NOT NULL,
				creator TEXT NOT NULL,
				effective date NOT NULL,
				message TEXT,
				period INT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS WindowWeek (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS WindowWeekDaySpan (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				day INTEGER NOT NULL,
				end INTEGER NOT NULL,
				start INTEGER NOT NULL,
				window_id INTEGER -- WindowWeek fk
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS WindowWeekDayOverride (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				created timestamp NOT NULL,
				creator TEXT NOT NULL,
				effective date NOT NULL,
				message TEXT,
				windowset TEXT NOT NULL
			);""")
