import datetime
import os
import unittest

from parentopticon import db

TEST_DB_PATH = "/tmp/parentopticon-test-db.sqlite"
def ensure_test_db_exists():
	if os.path.exists(TEST_DB_PATH):
		os.unlink(TEST_DB_PATH)

class DBTestCase(unittest.TestCase):
	def setUp(self):
		self.db = db.Connection()
		self.db.connect(TEST_DB_PATH)
		self.db.truncate_all()
	
class ProgramSessionTests(DBTestCase):
	def setUpClass():
		ensure_test_db_exists()

	def setUp(self):
		super().setUp()
		self.group_id = self.db.group_create("games")
		self.program_id = self.db.program_create("Minecraft", self.group_id)
		self.db.process_create("net.minecraft.client.main.Main", self.program_id)

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

	def test_session_list_since(self):
		"Can we list sessions since an arbitrary date?"
		self.db.program_session_create(
			end = None,
			program_id = 1,
			start = datetime.datetime(2020, 3, 1),
		)
		self.db.program_session_create(
			end = None,
			program_id = 2,
			start = datetime.datetime(2020, 2, 1),
		)
		moment = datetime.datetime(2020, 2, 14, 1, 0, 0)
		results = list(self.db.program_session_list_since(moment))
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0].program_id, 1)

	def test_session_list_open(self):
		"Can we list all the sessions that are still open?"
		self.db.program_session_create(
			end = None,
			program_id = 1,
			start = datetime.datetime(2020, 3, 1),
		)
		self.db.program_session_create(
			end = datetime.datetime(2020, 3, 3),
			program_id = 2,
			start = datetime.datetime(2020, 3, 2),
		)
		results = list(self.db.program_session_list_open())
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0].program_id, 1)

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
	
