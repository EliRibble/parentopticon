"Utilities for testing against the DB."
import os
import unittest

from parentopticon.db.connection import Connection
from parentopticon.db.tables import create_all, truncate_all, ProgramGroup

TEST_DB_PATH = "/tmp/parentopticon-test-db.sqlite"


class DBTestCase(unittest.TestCase):
	"Class that includes a test database."
	def cleanup_test_db(self):
		"Clean up any lingering test DB file."
		if os.path.exists(TEST_DB_PATH):
			os.unlink(TEST_DB_PATH)

	def setUp(self):
		"Set up test case, create a database."
		self.db = Connection()
		self.db.connect(TEST_DB_PATH)
		create_all(self.db)

	def tearDown(self):
		"Clean up the test case, clean the database."
		truncate_all(self.db)

def make_group(connection: Connection, name: str = "games") -> int:
	return ProgramGroup.insert(connection,
		minutes_monday=0,
		minutes_tuesday=0,
		minutes_wednesday=0,
		minutes_thursday=0,
		minutes_friday=0,
		minutes_saturday=0,
		minutes_sunday=0,
		minutes_weekly=0,
		minutes_monthly=0,
			name=name)
