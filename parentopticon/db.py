import collections
import logging
import sqlite3
from typing import Iterable, List, Optional

LOGGER = logging.getLogger(__name__)

Group = collections.namedtuple("Group", ("id", "name", "limit", "window_week"))
Limit = collections.namedtuple("Limit", ("id", "name", "daily", "weekly", "monthly"))
class WindowWeekDaySpan:
	def __init__(self, id_: int, day: int, end: int, start: int, window_id: int):
		self.id = id_
		self.day = day
		self.end = end
		self.start = start
		self.window_id = window_id

	@property
	def value(self) -> str:
		return "{}-{}".format(self.start, self.end)

class WindowWeekDay:
	def __init__(self, window_id: int, day: int, spans: List[WindowWeekDaySpan]):
		self.window_id = window_id
		self.day = day
		self.spans = sorted(spans, key=lambda s: s.start)

	@property
	def value(self) -> str:
		return ",".join(span.value for span in self.spans)

class WindowWeek:
	def __init__(self, id_: int, name: str, days: List[WindowWeekDay]):
		self.id = id_
		self.name = name
		self.days = days

	@property
	def monday(self):
		return self.days[0]

	@property
	def tuesday(self):
		return self.days[1]

	@property
	def wednesday(self):
		return self.days[2]

	@property
	def thursday(self):
		return self.days[3]

	@property
	def friday(self):
		return self.days[4]

	@property
	def saturday(self):
		return self.days[5]

	@property
	def sunday(self):
		return self.days[6]

class Connection:
	"Class that encapsulates all the interface to the DB."
	def __init__(self):
		self.connection = None
		self.cursor = None

	def connect(self):
		self.connection = sqlite3.connect("/usr/share/parentopticon/db.sqlite")
		self.cursor = self.connection.cursor()
		self._create_tables()

	def group_create(self, name: str, limit: Optional[int], window_week: Optional[int]) -> int:
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
				name TEXT NOT NULL
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
				end TEXT NOT NULL, 
				start TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramSession (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				end TEXT NOT NULL,
				start TEXT NOT NULL,
				program TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramGroupLimitBonus (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				amount INTEGER NOT NULL,
				created TEXT NOT NULL,
				creator TEXT NOT NULL,
				effective TEXT NOT NULL,
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
				created TEXT NOT NULL,
				creator TEXT NOT NULL,
				effective TEXT NOT NULL,
				message TEXT,
				windowset TEXT NOT NULL
			);""")
