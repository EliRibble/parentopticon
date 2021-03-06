import logging
import sqlite3
from typing import Any, Iterable, Optional, Tuple

import chryso.connection
from parentopticon.db import tables

LOGGER = logging.getLogger(__name__)

class Connection:
	"Class that encapsulates all the interface to the DB."
	def __init__(self):
		self.connection = None
		self.cursor = None

	def commit(self, *args, **kwargs) -> None:
		return self.connection.commit(*args, **kwargs)

	def connect(self, path: Optional[str] = "/usr/share/parentopticon/db.sqlite"):
		self.connection = sqlite3.connect(
			path,
			detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
		)
		self.cursor = self.connection.cursor()

	def execute(self, *args) -> Iterable[Tuple[Any]]:
		return self.cursor.execute(*args)

	def execute_commit_return(self, *args) -> int:
		"Execute a statement, commit it, return the rowid."
		self.cursor.execute(*args)
		self.connection.commit()
		return self.cursor.lastrowid

def create(uri: str):
	"Create a connection to the database."
	engine = chryso.connection.Engine(
		uri = uri,
		tables = [],
	)
	chryso.connection.store(engine)
	LOGGER.info("DB engine connection established.\n\t%s", engine.execute("SELECT version()").fetchone())
	return engine
