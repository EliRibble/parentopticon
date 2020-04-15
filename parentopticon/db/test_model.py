import datetime
import os
from typing import List, Optional
import unittest

from parentopticon.db import test_utilities
from parentopticon.db.model import ColumnInteger, ColumnText, Model

class ModelTests(test_utilities.DBTestCase):
	"Test all of our logic around the model class."
	class MyTable(Model):
		COLUMNS = {
			"id": ColumnInteger(autoincrement=True, primary_key=True),
			"count": ColumnInteger(),
			"name": ColumnText(null=True),
		}

	def _makerows(self, names: Optional[List[str]] = None):
		"Make a few rows. Useful for many tests."
		names = names or ["foo", "bar", "baz"]
		return {
			ModelTests.MyTable.insert(self.db, count=(i+1)*2, name=name)
			for i, name in enumerate(names)
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
			"name TEXT",
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

	def test_get_none(self):
		"Can we get None when the row does not exist?"
		result = ModelTests.MyTable.get(self.db, -1)
		self.assertIs(result, None)

	def test_list_all(self):
		"Can we get several rows from the table?"
		rowids = self._makerows()
		results = ModelTests.MyTable.list(self.db)
		self.assertEqual({result.id for result in results}, rowids)

	def test_list_some(self):
		"Can we get several rows from the table with a where clause?"
		rowids = self._makerows()
		results = ModelTests.MyTable.list_where(self.db, where="count >= 4")
		self.assertEqual({result.count for result in results}, {4, 6})

	def test_list_with_none(self):
		"Can we get a list where an item is NULL?"
		rowids = self._makerows(names=["foo", None, "bar"])
		results = ModelTests.MyTable.list(self.db, name=None)
		self.assertEqual({result.count for result in results}, {4})

	def test_search_not_found(self):
		"Can we search and not find something?"
		results = ModelTests.MyTable.search(self.db, name="sir-not-appearing")
		self.assertIs(results, None)

	def test_search_one(self):
		"Can we search and find a single row?"
		rowids = self._makerows()
		results = ModelTests.MyTable.search(self.db, name="foo")
		self.assertEqual(results.name, "foo")
		self.assertEqual(results.count, 2)

	def test_search_many(self):
		"Do we error when we have multiple matches?"
		self._makerows(names=["foo", "foo", "bar"])
		with self.assertRaises(ValueError):
			ModelTests.MyTable.search(self.db, name="foo")

	def test_search_with_none(self):
		"Do we properly search for NULL columns?"
		self._makerows(names=["foo", None, "bar"])
		results = ModelTests.MyTable.search(self.db, name=None)
		self.assertEqual(results.name, None)
		self.assertEqual(results.count, 4)
