import datetime
import os
import unittest

from parentopticon.db import test_utilities
from parentopticon.db import queries
from parentopticon.db.model import ColumnInteger, ColumnText, Model
from parentopticon.db.tables import Program, ProgramGroup, ProgramProcess, ProgramSession

class ProgramProcessTests(test_utilities.DBTestCase):
	"Test interactions between programs and processes."
	def setUp(self):
		super().setUp()
		self.programs = [
			Program.insert(self.db,
				name = "Minecraft",
			),
			Program.insert(self.db,
				name = "Terraria",
			),
		]
		self.processes = [
			ProgramProcess.insert(self.db,
				name = "net.minecraft.client.main.Main",
				program = self.programs[0],
			),
			ProgramProcess.insert(self.db,
				name = "minecraft-launcher",
				program = self.programs[0],
			),
			ProgramProcess.insert(self.db,
				name = "terraria.exe",
				program = self.programs[1],
			),
		]

	def test_list_program_by_process(self):
		"Can we get a list of programs by process?"
		result = queries.list_program_by_process(self.db)
		expected = {
			"net.minecraft.client.main.Main": "Minecraft",
			"minecraft-launcher": "Minecraft",
			"terraria.exe": "Terraria",
		}
		self.assertEqual(result, expected)

class ProgramSessionTests(test_utilities.DBTestCase):
	def setUp(self):
		super().setUp()
		self.group_id = ProgramGroup.insert(self.db,
			minutes_monday=0,
			minutes_tuesday=0,
			minutes_wednesday=0,
			minutes_thursday=0,
			minutes_friday=0,
			minutes_saturday=0,
			minutes_sunday=0,
			minutes_weekly=0,
			minutes_monthly=0,
			name="games")
		self.program_id = Program.insert(
			self.db,
			name="Minecraft",
			program_group=self.group_id)
		ProgramProcess.insert(self.db, name="net.minecraft.client.main.Main", program=self.program_id)

	def test_session_close(self):
		"Can we close a session after opening it?"
		program_session_id = ProgramSession.insert(
			self.db,
			end = None,
			start = datetime.datetime.now(),
			program = self.program_id,
		)
		program_session = ProgramSession.get(self.db, program_session_id)
		self.assertEqual(program_session.end, None)

		queries.program_session_close(self.db, program_session.id)

		program_session = ProgramSession.get(self.db, program_session_id)
		self.assertNotEqual(program_session.end, None)

	def test_session_list_since(self):
		"Can we list sessions since an arbitrary date?"
		queries.program_session_create(
			self.db,
			end = None,
			program_id = 1,
			start = datetime.datetime(2020, 3, 1),
		)
		queries.program_session_create(
			self.db,
			end = None,
			program_id = 2,
			start = datetime.datetime(2020, 2, 1),
		)
		moment = datetime.datetime(2020, 2, 14, 1, 0, 0)
		results = list(queries.program_session_list_since(self.db, moment))
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0].program_id, 1)

	def test_session_list_open(self):
		"Can we list all the sessions that are still open?"
		results = list(queries.program_session_list_open(self.db))
		self.assertEqual(len(results), 0)
		queries.program_session_create(
			self.db,
			end = None,
			program_id = 1,
			start = datetime.datetime(2020, 3, 1),
		)
		queries.program_session_create(
			self.db,
			end = datetime.datetime(2020, 3, 3),
			program_id = 2,
			start = datetime.datetime(2020, 3, 2),
		)
		results = list(queries.program_session_list_open(self.db))
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0].program_id, 1)

	def test_session_ensure_exists_new(self):
		"Can we create a session when one doesn't already exist?"
		results = queries.program_session_ensure_exists(self.db, self.program_id)
		program_session = queries.program_session_get_open(self.db, self.program_id)
		self.assertEqual(program_session.id_, results)

	def test_session_ensure_exists_old(self):
		"Can we return a session when it already exists?"
		program_session_id = queries.program_session_create(
			self.db,
			end = None,
			start = datetime.datetime.now(),
			program_id = self.program_id,
		)
		results = queries.program_session_ensure_exists(self.db, self.program_id)
		self.assertEqual(program_session_id, results)
	
