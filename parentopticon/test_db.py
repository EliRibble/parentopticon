import datetime
import os
import unittest

from parentopticon import db

class ProgramSessionTests(unittest.TestCase):
	def setUp(self):
		self.db = db.Connection()
		test_db_path = "/tmp/parentopticon-test-db.sqlite"
		if os.path.exists(test_db_path):
			os.unlink(test_db_path)
		self.db.connect(test_db_path)
		self.group_id = self.db.group_create("games")
		self.program_id = self.db.program_create("Minecraft", self.group_id)
		self.db.process_create("net.minecraft.client.main.Main", self.program_id)

	def test_session_ensure_exists_new(self):
		"Can we create a session when one doesn't already exist?"
		results = self.db.program_session_ensure_exists(self.program_id)
		program_session = self.db.program_session_get_open(self.program_id)
		self.assertEqual(program_session.id, results)

	def test_session_ensure_exists_old(self):
		"Can we return a session when it already exists?"
		program_session_id = self.db.program_session_create(
			end = None,
			start = datetime.datetime.now(),
			program_id = self.program_id,
		)
		results = self.db.program_session_ensure_exists(self.program_id)
		self.assertEqual(program_session_id, results)
	
	def test_session_close(self):
		"Can we close a session after opening it?"
		program_session_id = self.db.program_session_create(
			end = None,
			start = datetime.datetime.now(),
			program_id = self.program_id,
		)
		program_session = self.db.program_session_get(program_session_id)
		self.assertEqual(program_session.end, None)

		self.db.program_session_close(program_session_id)

		program_session = self.db.program_session_get(program_session_id)
		self.assertNotEqual(program_session.end, None)

