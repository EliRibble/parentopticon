import datetime
import unittest

import freezegun

from parentopticon import db, enforcement, test_db

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
		
class GetProgramSessionsCurrentTests(test_db.DBTestCase):
	"Test enforcement.get_program_sessions_current."
	def setUp(self):
		super().setUp()
		self.group_id = self.db.group_create("games")
		self.programs = [
			self.db.program_create("Minecraft", self.group_id),
			self.db.program_create("Terraria", self.group_id),
		]

	@freezegun.freeze_time("2020-02-02 11:00:00")
	def test_week_split(self):
		"Can we capture time spent this week outside this month?"
		now = datetime.datetime

		# program session for this week, but not this month
		self.db.program_session_create(
			end = datetime.datetime(2020, 2, 1, 10, 0, 0),
			start = datetime.datetime(2020, 2, 1, 9, 10, 0),
			program_id = self.programs[0],
		)
		# program session last month, last week
		self.db.program_session_create(
			end = datetime.datetime(2020, 1, 25, 10, 0, 0),
			start = datetime.datetime(2020, 1, 25, 9, 0, 0),
			program_id = self.programs[1],
		)
		# program session earlier today
		self.db.program_session_create(
			end = datetime.datetime(2020, 2, 2, 10, 0, 0),
			start = datetime.datetime(2020, 2, 2, 9, 0, 0),
			program_id = self.programs[1],
		)
		result = enforcement.get_program_sessions_current(self.db)
		self.assertEqual(len(result), 2)
			
		
