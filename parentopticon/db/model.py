import collections
import datetime
import logging
import sqlite3
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from parentopticon.db.connection import Connection

LOGGER = logging.getLogger(__name__)

StatementAndBinding = Tuple[str, Iterable[Any]]

class Column:
	"Represents a single column on a table."
	TYPENAME = "NONE"
	def __init__(self,
		autoincrement: bool = False,
		null: bool = True,
		primary_key: bool = False) -> None:
		self.autoincrement = autoincrement
		self.null = null
		self.primary_key = primary_key

	def create_statement(self, name):
		"Get the SQL statement to create this column."
		attributes = []
		if self.primary_key:
			attributes.append("PRIMARY KEY")
		if self.autoincrement:
			attributes.append("AUTOINCREMENT")
		if not self.null:
			attributes.append("NOT NULL")
		if attributes:
			return " ".join((
				name,
				self.TYPENAME,
				" ".join(attributes),
			))
		return " ".join((name, self.TYPENAME))

class ColumnForeignKey(Column):
	"Represents a column that is a foreign key to another table."
	TYPENAME = "INTEGER"
	def __init__(self,
		target_table: "Model",
		null: bool = True,
		primary_key: bool = False) -> None:
		super().__init__(
			autoincrement=False,
			null=null,
			primary_key=False)


class ColumnDate(Column):
	"Represents a single date column."
	TYPENAME = "date"

class ColumnDatetime(Column):
	"Represents a single date and time column."
	TYPENAME = "timestamp"

class ColumnText(Column):
	"Represents a single text column on a table."
	TYPENAME = "TEXT"

class ColumnInteger(Column):
	"Represents a single integer column on a table."
	TYPENAME = "INTEGER"

class Model:
	"Represents an object from a database."
	COLUMNS = {}

	def __init__(self, **kwargs) -> None:
		for k, v in kwargs.items():
			setattr(self, k, v)

	@classmethod
	def columns(cls) -> Mapping[str, Column]:
		return cls.COLUMNS

	@classmethod
	def columns_sorted(cls) -> Iterable[Tuple[str, Column]]:
		"Get all of the columns for this table in sorted order."
		columns = cls.columns()
		sorted_keys = sorted(columns.keys())
		for k in sorted_keys:
			yield (k, cls.COLUMNS[k])

	@classmethod
	def create_statement(cls):
		"Get the SQL statement to create the table."
		column_lines = [column.create_statement(name) for name, column in cls.columns_sorted()]
		column_content = ",\n".join(column_lines)
		return "CREATE TABLE IF NOT EXISTS {} (\n{}\n);".format(
			cls.__name__,
			column_content,
		)

	@classmethod
	def get(cls, connection: Connection, id_: int) -> Optional["Model"]:
		"Get a single row by its ID"
		select_statement = cls.select_statement(
			where="id = ?")
		row = connection.execute(select_statement, (id_,)).fetchone()
		if row is None:
			return row
		column_names = [k for k, _ in cls.columns_sorted()]
		data = {k: v for k, v in zip(column_names, row)}
		return cls(**data)

	@classmethod
	def insert(cls, connection: Connection, **kwargs) -> int:
		"Insert a new row into the table. Return rowid."
		statement, values = cls.insert_statement(**kwargs)
		return connection.execute_commit_return(statement, values)

	@classmethod
	def insert_statement(cls, **kwargs) -> StatementAndBinding:
		"""Get the SQL statement for inserting into this table.

		Returns:
			The SQL statement and the list of parameters for
			the bindings within the statement.
		"""
		kwarg_keys_sorted = sorted(kwargs.keys())
		kwarg_keys_quoted = ["\"{}\"".format(k) for k in kwarg_keys_sorted]
		placeholders = ", ".join("?" * len(kwargs))
		values = [kwargs[k] for k in kwarg_keys_sorted]
		return ("INSERT INTO {} ({}) VALUES ({})".format(
			cls.__name__,
			", ".join(kwarg_keys_quoted),
			placeholders,
		), values)

	@classmethod
	def list(cls,
		connection: Connection,
		**kwargs,
		) -> Iterable["Model"]:
		"""List rows for this table.

		Args:
			connection: The DB connection to use.
			kwargs: column names to values that go into a WHERE clause.
		Returns:
			Matching rows as class instances.
		"""
		where_statement, bindings = kwargs_to_where_and_bindings(**kwargs)
		return cls.list_where(connection, where_statement, bindings)


	@classmethod
	def list_where(cls,
		connection: Connection,
		where: Optional[str] = None,
		bindings: Iterable[Any] = None,
		) -> Iterable["Model"]:
		"""List rows for this table.

		Args:
			connection: The DB connection to use.
			where: An optional 'WHERE' clause, minus the 'WHERE'.
			bindings: Additional bindings for the where clause.
		Returns:
			Matching rows as class instances.
		"""
		select_statement = cls.select_statement(where=where)
		bindings = bindings or ()
		try:
			rows = connection.execute(select_statement, bindings)
		except sqlite3.OperationalError as ex:
			LOGGER.error("%s\n\nwhere: %s\nbindings: %s", ex, where, bindings)
			raise
		column_names = [k for k, _ in cls.columns_sorted()]
		for row in rows:
			data = {k: v for k, v in zip(column_names, row)}
			yield cls(**data)

	@classmethod
	def search(cls, connection: Connection, **kwargs) -> Optional["Model"]:
		"""Search for a single row."""
		where, bindings = kwargs_to_where_and_bindings(**kwargs)
		select_statement = cls.select_statement(where=where)
		rows = connection.execute(select_statement, bindings).fetchall()
		if len(rows) == 0:
			return None
		elif len(rows) == 1:
			row = rows[0]
			column_names = [k for k, _ in cls.columns_sorted()]
			data = {k: v for k, v in zip(column_names, row)}
			return cls(**data)
		else:
			raise ValueError("Expected to find at most one row, found {}".format(len(rows)))

	@classmethod
	def select_statement(cls, where=None) -> str:
		"""Get the SQL statement for selecting a row from this table.

		Returns:
			The SQL statement for getting a single row.
		"""
		column_names = [k for k, _ in cls.columns_sorted()]
		return "SELECT {} FROM {} {}".format(
			", ".join(column_names),
			cls.__name__,
			("WHERE " + where) if where else "",
		)

	@classmethod
	def truncate_statement(cls) -> str:
		"Get the statement to truncate the table."
		return "DELETE FROM {}".format(cls.__name__)

def kwargs_to_where_and_bindings(**kwargs) -> Tuple[Optional[str], List[Any]]:
	"Turn kwargs into a where statement and matching bindings."
	if not kwargs:
		return None, []
	where_parts = []
	bindings = []
	for k, v in kwargs.items():
		if v is None:
			where_parts.append("{} IS NULL".format(k))
		else:
			where_parts.append("{} = ?".format(k))
			bindings.append(v)
	where = " AND ".join(where_parts)
	return where, bindings
