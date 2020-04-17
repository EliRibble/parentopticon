import datetime
import unittest

import freezegun

from parentopticon import enforcement
from parentopticon.db import test_utilities
from parentopticon.db.tables import Program, ProgramGroup, ProgramSession

class GetLimitMinutesLeft(unittest.TestCase):
	"Test enforcement.get_limit_minutes_left"
	def setUp(self):
		self.limit = db.Limit(
			id = 1,
			name = "games_limit",
			daily = 60,
			weekly = 300,
			monthly = 1000,
		)
		days = [
			db.WindowWeekDay(
				id_ = 1,
				day = i,
			)
		]
		self.window_week = db.WindowWeek(
			id_ = 1,
			name = "games_window",
			days = days,
		)
		self.group = db.Group(
			id = 1,
			name = "Minecraft",
			limit = self.limit,
			window_week = self.window_week,
		)
		self.program = db.Program(
			id = 1,
			name = "Minecraft",
			group = self.group,
			processes = ["java"],
		)
		
class GetProgramSessionsCurrentTests(test_utilities.DBTestCase):
	"Test enforcement.get_program_sessions_current."
	def setUp(self):
		super().setUp()
		self.group_id = test_utilities.make_group(self.db)
		self.programs = [
			Program.insert(self.db, name="Minecraft", program_group=self.group_id),
			Program.insert(self.db, name="Terraria", program_group=self.group_id),
		]

	def test_week_split(self):
		"Can we capture time spent this week outside this month?"
		# program session for this week, but not this month
		ProgramSession.insert(
			self.db,
			end = datetime.datetime(2020, 2, 1, 10, 0, 0),
			hostname = "testhost",
			pids = "",
			program = self.programs[0],
			start = datetime.datetime(2020, 2, 1, 9, 10, 0),
			username = "testuser",
		)
		# program session last month, last week
		ProgramSession.insert(
			self.db,
			end = datetime.datetime(2020, 1, 25, 10, 0, 0),
			hostname = "testhost",
			pids = "",
			program = self.programs[1],
			start = datetime.datetime(2020, 1, 25, 9, 0, 0),
			username = "testuser",
		)
		# program session earlier today
		ProgramSession.insert(
			self.db,
			end = datetime.datetime(2020, 2, 2, 10, 0, 0),
			hostname = "testhost",
			pids = "",
			program = self.programs[1],
			start = datetime.datetime(2020, 2, 2, 9, 0, 0),
			username = "testuser",
		)
		with freezegun.freeze_time("2020-02-02 11:00:00"):
			result = enforcement.get_program_sessions_current(self.db)
		self.assertEqual(len(result), 2)
			
		
