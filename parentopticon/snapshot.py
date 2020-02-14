"""
Module for logic around getting a snapshot of what the system is doing.
"""
import logging
import pprint
import psutil

from parentopticon import db


LOGGER = logging.getLogger(__name__)


def take(db_connection: db.Connection, timespan: int) -> None:
	"""Take a snapshot of the running programs.

	Args:
		db_connection: Connection to the database to use
		timespan: The amount of time in seconds between snapshots.
	"""
	programs = list(db_connection.program_list())
	program_ids = {program.id for program in programs}
	programs_seen = set()
	for process in psutil.process_iter(attrs=["cmdline", "exe", "name", "username"]):
		for program in programs:
			for program_process in program.processes:
				if program_process.name in process.cmdline():
					programs_seen.add(program.id)
	for program_id in programs_seen:
		session = db_connection.program_session_ensure_exists(program_id)
	for program_id in program_ids - programs_seen:
		db_connection.program_session_ensure_closed(program_id)

