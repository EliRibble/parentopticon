import datetime
import os
import unittest

from parentopticon.db import test_utilities
from parentopticon.db.model import ColumnInteger, ColumnText, Model

class ModelTests(test_utilities.DBTestCase):
	"Test all of our logic around the model class."
	class MyTable(Model):
		COLUMNS = {
			"id": ColumnInteger(autoincrement=True, primary_key=True),
			"count": ColumnInteger(),
			"name": ColumnText(null=False),
		}

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


