import datetime
import os
import unittest

from parentopticon.db import test_utilities

class ConnectionTestCase(test_utilities.DBTestCase):
	"Test making a DB connection."
	def test_file_creation_and_cleanup(self):
		"Do we create the DB file and clean it up?"
		self.assertTrue(os.path.exists(test_utilities.TEST_DB_PATH))
