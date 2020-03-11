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

class ModelTests(DBTestCase):
	"Test all of our logic around the model class."
	class MyTable(db.Model):
		COLUMNS = {
			"id": db.ColumnInteger(autoincrement=True, primary_key=True),
			"count": db.ColumnInteger(),
			"name": db.ColumnText(null=False),
		}

	def setUpClass():
		ensure_test_db_exists()

	def setUp(self):
		super().setUp()
		self.db.execute_commit_return(ModelTests.MyTable.create_statement())
		self.db.execute_commit_return(ModelTests.MyTable.truncate_statement())

	def test_create_statement(self):
		"Can we get a proper create table clause?"
		result = ModelTests.MyTable.create_statement()
		expected = "\n".join((
			"CREATE TABLE IF NOT EXISTS MyTable (",
			"count INTEGER,",
			"id INTEGER PRIMARY KEY AUTOINCREMENT,",
			"name TEXT NOT NULL",
			");",
		))
		self.assertEqual(result, expected)

	def test_insert(self):
		"Can we insert a row into a table?"
		rowid = ModelTests.MyTable.insert(self.db, count=3, name="foobar")
		found = self.db.execute("SELECT count, name FROM MyTable").fetchall()
		self.assertEqual(len(found), 1)
		
	def test_get(self):
		"Can we get a row from the table?"
		rowid = ModelTests.MyTable.insert(self.db, count=3, name="foobar")
		result = ModelTests.MyTable.get(self.db, rowid)
		self.assertEqual(result.id, rowid)
		self.assertEqual(result.count, 3)
		self.assertEqual(result.name, "foobar")

	def test_list_all(self):
		"Can we get several rows from the table?"
		rowids = {
			ModelTests.MyTable.insert(self.db, count=2, name="foo"),
			ModelTests.MyTable.insert(self.db, count=4, name="bar"),
			ModelTests.MyTable.insert(self.db, count=6, name="baz"),
		}
		results = ModelTests.MyTable.list(self.db)
		self.assertEqual({result.id for result in results}, rowids)

	def test_list_some(self):
		"Can we get several rows from the table with a where clause?"
		rowids = [
			ModelTests.MyTable.insert(self.db, count=2, name="foo"),
			ModelTests.MyTable.insert(self.db, count=4, name="bar"),
			ModelTests.MyTable.insert(self.db, count=6, name="baz"),
		]
		results = ModelTests.MyTable.list(self.db, where="count >= 4")
		self.assertEqual({result.count for result in results}, {4, 6})


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
	
