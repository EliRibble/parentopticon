import sqlite3

class Connection:
	"Class that encapsulates all the interface to the DB."
	def __init__(self):
		self.connection = None
		self.cursor = None

	def connect(self):
		self.connection = sqlite3.connect("/usr/share/parentopticon/db.sqlite")
		self.cursor = self.connection.cursor()
		self._create_tables()

	def _create_tables(self):
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS Program (
				name TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramGroupLimit (
				name TEXT NOT NULL,
				daily INTEGER NOT NULL,
				weekly INTEGER NOT NULL,
				monthly INTEGER NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS WindowWeek (
				name TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS WindowWeekDayWindow (
				day INTEGER NOT NULL,
				end TEXT NOT NULL,
				start TEXT NOT NULL,
				windowweek INTEGER -- WindowWeek fk
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramGroup (
				name TEXT NOT NULL,
				group_limit INTEGER -- Limit FK
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS UserSession (
				end TEXT NOT NULL, 
				start TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramSession (
				end TEXT NOT NULL,
				start TEXT NOT NULL,
				program TEXT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS ProgramGroupLimitBonus (
				amount INTEGER NOT NULL,
				created TEXT NOT NULL,
				creator TEXT NOT NULL,
				effective TEXT NOT NULL,
				message TEXT,
				period INT NOT NULL
			);""")
		self.cursor.execute(
			"""CREATE TABLE IF NOT EXISTS WindowWeekDayOverride (
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
