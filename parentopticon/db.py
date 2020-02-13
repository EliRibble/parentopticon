import collections
import logging
import sqlite3
import typing

LOGGER = logging.getLogger(__name__)

Limit = collections.namedtuple("Limit", ("id", "name", "daily", "weekly", "monthly"))


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
			"SELECT id, name, daily, weekly, monthly FROM ProgramGroupLimit WHERE rowid = ?", (limit_id,))
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
			"""CREATE TABLE IF NOT EXISTS WindowWeek (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS WindowWeekDayWindow (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				day INTEGER NOT NULL,
				end TEXT NOT NULL,
				start TEXT NOT NULL,
				windowweek INTEGER -- WindowWeek fk
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
			"""CREATE TABLE IF NOT EXISTS WindowWeekDayOverride (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				created TEXT NOT NULL,
				creator TEXT NOT NULL,
				effective TEXT NOT NULL,
				message TEXT,
				windowset TEXT NOT NULL
			);""")

# Tables
#  UserSession
#   end: datetime
#   start: datetime
#  ProgramSession
#   end: datetime
#   start: datetime
#   program: str
#  LimitBonus
#   amount: int
#   created: datetime
#   creator: str
#   effective: datetime
#   message: str
#   period: enum(day, week, month)
#  WindowWeekDayOverride
#   created: datetime
#   creator: str
#   effective: date
#   message: str
#   windowset: str
