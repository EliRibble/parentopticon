import datetime
import os
import unittest
from typing import Optional

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
		self.group_id = test_utilities.make_group(self.db)
		self.program_id = Program.insert(
			self.db,
			name="Minecraft",
			program_group=self.group_id)
		ProgramProcess.insert(self.db, name="net.minecraft.client.main.Main", program=self.program_id)

	def make_program_session(self,
		end: Optional[datetime.datetime] = None,
		start: Optional[datetime.datetime] = None) -> int:
		return ProgramSession.insert(self.db,
			end = end,
			hostname = "testhost",
			pids = "",
			program = self.program_id,
			start = start or datetime.datetime.now(),
			username = "testuser",
		)

	def test_session_close(self):
		"Can we close a session after opening it?"
		program_session_id = self.make_program_session()
		program_session = ProgramSession.get(self.db, program_session_id)
		self.assertEqual(program_session.end, None)

		queries.program_session_close(self.db, program_session.id)

		program_session = ProgramSession.get(self.db, program_session_id)
		self.assertNotEqual(program_session.end, None)

	def test_session_list_since(self):
		"Can we list sessions since an arbitrary date?"
		self.make_program_session(start=datetime.datetime(2020, 3, 1))
		self.make_program_session(start=datetime.datetime(2020, 2, 1))
		moment = datetime.datetime(2020, 2, 14, 1, 0, 0)
		results = list(queries.program_session_list_since(self.db, moment))
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0].program_id, self.program_id)

	def test_session_create_or_add_create(self):
		"Can we create a session when one does not exist?"
		program_session_id = queries.program_session_create_or_add(
			self.db,
			elapsed_seconds = 0,
			hostname="testhost",
			program_name = "Minecraft",
			pids = [],
			username="testuser",
		)
		results = ProgramSession.get(self.db, program_session_id)
		self.assertEqual(results.program, self.program_id)
