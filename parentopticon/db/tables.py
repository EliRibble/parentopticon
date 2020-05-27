import collections
import datetime
import logging
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from parentopticon.db.connection import Connection
from parentopticon.db.model import ColumnBoolean, ColumnDate, ColumnDatetime, ColumnForeignKey, ColumnInteger, ColumnText, Model

LOGGER = logging.getLogger(__name__)

Group = collections.namedtuple("Group", ("id", "name", "limit", "window_week"))
Process = collections.namedtuple("Process", ("id", "name", "program_id"))
Program = collections.namedtuple("Program", ("id", "name", "group", "processes"))

class OneTimeMessage(Model):
	"A message to send once to a given person."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"content": ColumnText(null=False),
		"hostname": ColumnText(null=True),
		"created": ColumnDatetime(null=False),
		"sent": ColumnDatetime(null=True),
		"username": ColumnText(null=True),
	}

class ProgramGroup(Model):
	"A group of several programs tracked together."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"name": ColumnText(null=False),
		"minutes_monday": ColumnInteger(null=False),
		"minutes_tuesday": ColumnInteger(null=False),
		"minutes_wednesday": ColumnInteger(null=False),
		"minutes_thursday": ColumnInteger(null=False),
		"minutes_friday": ColumnInteger(null=False),
		"minutes_saturday": ColumnInteger(null=False),
		"minutes_sunday": ColumnInteger(null=False),
		"minutes_weekly": ColumnInteger(null=False),
		"minutes_monthly": ColumnInteger(null=False),
	}

class Program(Model):
	"A program that can run on a computer that we track."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"name": ColumnText(null=False),
		"program_group": ColumnForeignKey(ProgramGroup),
	}

class ProgramGroupBonus(Model):
	"Bonus time for a program group."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"amount_minutes": ColumnInteger(null=False),
		"created": ColumnDatetime(null=False),
		"creator": ColumnText(null=False),
		"effective_date": ColumnDate(null=False),
		"message": ColumnText(null=False),
		"program_group": ColumnForeignKey(ProgramGroup),
	}

class ProgramProcess(Model):
	"A process that a program may run on a system."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"name": ColumnText(null=False),
		"program": ColumnForeignKey(Program),
	}

class ProgramSession(Model):
	"A session using a particular program."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"hostname": ColumnText(null=False),
		"end": ColumnDatetime(null=True),
		"pids": ColumnText(null=False),
		"program": ColumnForeignKey(Program),
		"start": ColumnDatetime(null=False),
		"username": ColumnText(null=False),
	}

	@property
	def duration(self) -> Optional[datetime.timedelta]:
		"Get the duration of the session, if possible."
		if self.start and self.end:
			return self.end - self.start

class WebsiteVisit(Model):
	"A single visit to a website."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"at": ColumnDatetime(null=False),
		"hostname": ColumnText(null=False),
		"incognito": ColumnBoolean(null=False),
		"url": ColumnText(null=False),
		"username": ColumnText(null=False),
	}

class WindowWeekDaySpanOverride(Model):
	"An override for a single day in a window week."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"created": ColumnDatetime(null=False),
		"creator": ColumnText(null=False),
		"effective": ColumnDate(null=False),
		"message": ColumnText(null=False),
	}

class WindowWeekDaySpan(Model):
	"A span of time for a day of a week window."
	COLUMNS = {
		"id": ColumnInteger(autoincrement=True, primary_key=True),
		"day": ColumnInteger(null=False),
		"end": ColumnDatetime(null=True),
		"start": ColumnDatetime(null=False),
		"window_name": ColumnText(null=False),
	}
		
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

def truncate_all(connection: Connection) -> None:
	connection.cursor.execute(ProgramGroup.truncate_statement())
	connection.cursor.execute(ProgramGroupBonus.truncate_statement())
	connection.cursor.execute(Program.truncate_statement())
	connection.cursor.execute(ProgramProcess.truncate_statement())
	connection.cursor.execute(ProgramSession.truncate_statement())
	connection.cursor.execute(WebsiteVisit.truncate_statement())
	connection.cursor.execute(WindowWeekDaySpan.truncate_statement())
	connection.cursor.execute(WindowWeekDaySpanOverride.truncate_statement())
	connection.commit()

def create_all(connection: Connection):
	LOGGER.info("Ensuring DB tables exist.")
	connection.cursor.execute(OneTimeMessage.create_statement())
	connection.cursor.execute(ProgramGroup.create_statement())
	connection.cursor.execute(ProgramGroupBonus.create_statement())
	connection.cursor.execute(Program.create_statement())
	connection.cursor.execute(ProgramProcess.create_statement())
	connection.cursor.execute(ProgramSession.create_statement())
	connection.cursor.execute(WebsiteVisit.create_statement())
	connection.cursor.execute(WindowWeekDaySpan.create_statement())
	connection.cursor.execute(WindowWeekDaySpanOverride.create_statement())
	connection.commit()
	LOGGER.info("DB tables exist.")
