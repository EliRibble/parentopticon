import collections
import logging
import sqlite3
import typing

LOGGER = logging.getLogger(__name__)

Limit = collections.namedtuple("Limit", ("id", "name", "daily", "weekly", "monthly"))
WindowWeek = collections.namedtuple("Window", (
	"id",
	"name",
	"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"))

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
	def __init__(self, window_id: int, day: int, spans: typing.List[WindowWeekDaySpan]):
		self.window_id = window_id
		self.day = day
		self.spans = sorted(spans, key=lambda s: s.start)

	@property
	def value(self) -> str:
		return ",".join(span.value for span in self.spans)

class Connection:
	"Class that encapsulates all the interface to the DB."
	def __init__(self):
		self.connection = None
		self.cursor = None

	def connect(self):
		self.connection = sqlite3.connect("/usr/share/parentopticon/db.sqlite")
		self.cursor = self.connection.cursor()
		self._create_tables()

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

	def limit_list(self) -> typing.List[Limit]:
		return [Limit(
			id = data[0],
			name = data[1],
			daily = data[2],
			weekly = data[3],
			monthly = data[4],
		) for data in self.cursor.execute(
			"SELECT id, name, daily, weekly, monthly FROM ProgramGroupLimit")]

	def window_week_create(self, name: str) -> int:
		self.cursor.execute(
			"INSERT INTO WindowWeek (name) VALUES (?)",
			(name,))
		self.connection.commit()
		return self.cursor.lastrowid

	def window_week_get(self, window_id: int) -> WindowWeek:
		monday = self.window_week_day_get(window_id, 0)
		tuesday = self.window_week_day_get(window_id, 1)
		wednesday = self.window_week_day_get(window_id, 2)
		thursday = self.window_week_day_get(window_id, 3)
		friday = self.window_week_day_get(window_id, 4)
		saturday = self.window_week_day_get(window_id, 5)
		sunday = self.window_week_day_get(window_id, 6)
		self.cursor.execute(
			"SELECT id, name FROM WindowWeek WHERE id = ?", (window_id,))
		data = self.cursor.fetchone()
		return WindowWeek(
			id = data[0],
			name = data[1],
			monday = monday,
			tuesday = tuesday,
			wednesday = wednesday,
			thursday = thursday,
			friday = friday,
			saturday = saturday,
			sunday = sunday,
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
				group_limit INTEGER -- Limit FK
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
