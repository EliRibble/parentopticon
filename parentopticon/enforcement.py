"""
Module for handling enforcement logic.
"""
import datetime
from enum import Enum
from typing import Iterable

from parentopticon import ui
from parentopticon.db import queries
from parentopticon.db.connection import Connection
from parentopticon.db.tables import Program, ProgramSession

class ActionType(Enum):
	# Kill a program
	kill = "kill"
	# Show a warning
	warn = "warn"

class Action:
	def __init__(self, type_: ActionType, content: str) -> None:
		self.content = content
		self.type = type_

def do(action: Action) -> None:
	"Do whatever the action says to do."
	if action.type == ActionType.kill:
		kill(action.content)
	elif action.type == ActionType.warn:
		ui.show_alert(action.content)
	else:
		raise Exception("This should never happen.")

	
def get_minutes_left(program_sessions: Iterable[ProgramSession], program: Program) -> int:
	"Get the minutes left for a given program, rounded up."
	# Get all the restrictions that apply to this program
	window_week = program.group.window_week
	window_minutes = window_week.minutes_left(datetime.datetime.now())
	if window_minutes == 0:
		return 0
	limit_minutes = get_limit_minutes_left(program_sessions, program)


def get_limit_minutes_left(program_sessions: Iterable[ProgramSession], program: Program) -> int:
	"Get the minutes left for a program limit."
	now = datetime.datetime.now()
	limit = program.group.limit
	sessions_today = (
		ps for ps in program_sessions \
		if ps.program_id == program.id and \
		ps.start.isocalendar()[2] == now.isocalendar()[2])
	sessions_this_week = (
		ps for ps in program_sessions \
		if ps.program_id == program.id and \
		ps.start.isocalendar()[1] == now.isocalendar()[1])
	sessions_this_month = (
		ps for ps in program_sessions \
		if ps.program_id == program.id and \
		ps.start.month == now.month)

	minutes_today = _total_minutes(sessions_today)
	minutes_this_week = _total_minutes(sessions_this_week)
	minutes_this_month = _total_minutes(sessions_this_month)

	left_today = limit.daily - minutes_today
	left_this_week = limit.weekly - minutes_this_week
	left_this_month = limit.monthly - minutes_this_month
	
	return min((left_today, left_this_week, left_this_month))


def get_program_sessions_current(connection: Connection) -> Iterable[ProgramSession]:
	"""Get the program sessions that are interesting to enforcement.

	This includes all sessions, opened and closed, since the start
	of the earlier of the start of the week or month as well as any
	open sessions.
	"""
	now = datetime.datetime.now()
	program_sessions_open = list(ProgramSession.list(connection, end=None))
	month_start = datetime.datetime(
		year = now.year,
		month = now.month,
		day = 1,
		hour = 0,
		minute = 0,
		second = 0,
	)
	week_start = now - datetime.timedelta(days=now.isoweekday()-1)
	week_start = datetime.datetime(
		year = week_start.year,
		month = week_start.month,
		day = week_start.day,
		hour = 0,
		minute = 0,
		second = 0,
	)
	earliest = min(month_start, week_start)
	program_sessions_past = list(queries.program_session_list_since(connection, earliest))
	return program_sessions_past + program_sessions_open

def go(db_connection: Connection) -> None:
	"Check enforcement, give warnings, shutdown programs."
	# Get all of the open sessions - if there are no
	# open sessions there's nothing to enforce.
	program_sessions = get_program_sessions_current()
	for ops in (ps for ps in program_sessions if ps.end is None):
		program = db_connection.program_get(ops.program_id)
		minutes_left = get_minutes_left(program_sessions, program)
		if minutes_left == 15:
			ui.show_alert("Finish up!",
				"You have {} minutes left to play {}.\n"
				"You should finish up!".format(
					minutes_left, ops.program.name))
		elif minutes_left == 5:
			ui.show_alert("Almost done!",
				"You have {} minutes left on {}.\n"
				"You should exit soon.".format(
					minutes_left, ops.program.name))
		elif minutes_left == 1:
			ui.show_alert("Exit now!",
				"You have just 1 minute left on {}.\n"
				"You should exit now.".format(
					ops.program.name))
		else:
			kill(ops.program),
			ui.show_alert("You're done.",
				"I've killed {}. You may have lost progress/work/data.\n"
				"Next time exit cleanly yourself.".format(ops.program.name))

def kill(program: Program) -> None:
	"Forcefully kill the program."
	
			
def _total_minutes(program_sessions: Iterable[ProgramSession]) -> int:
	"Get total minutes consumed by the given program sessions."
