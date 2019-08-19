"""
Module for logic around getting a snapshot of what the system is doing.
"""
import logging
import psutil

LOGGER = logging.getLogger(__name__)


def take() -> None:
	for process in psutil.process_iter(attrs=["name", "username"]):
		LOGGER.info("Found %s from user %s", process.name(), process.username())
		
