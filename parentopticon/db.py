import sqlite3

class Connection:
	"Class that encapsulates all the interface to the DB."
	def __init__(self):
		self.connection = None
		self.cursor = None

	def connect(self):
		self.connection = sqlite3.connect("/usr/share/parentopticon/db.sqlite")
		self.cursor = connection.cursor()
		self._create_tables()

	def _create_tables(self):
		self.cursor.execute("""CREATE TABLE program (name TEXT, path TEXT)""")
		self.cursor.execute("""CREATE TABLE """)

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
