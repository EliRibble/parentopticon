"""
Module for logic around getting a snapshot of what the system is doing.
"""
import logging
import pprint
import psutil
from typing import Iterable, Mapping


LOGGER = logging.getLogger(__name__)


def take(process_to_program: Mapping[str, str]) -> Mapping[int, str]:
	"""Take a snapshot of the running programs.

	Args:
		process_to_program: A mapping of process names to programs.
	Returns:
		A mapping of pid to programs that are running.
	"""
	pid_to_program = {}
	for process in psutil.process_iter(attrs=["cmdline", "exe", "name", "username", "pid"]):
		for k, v in process_to_program.items():
			if k in process.cmdline():
				pid_to_program[process.pid] = v
	return pid_to_program
