"""
Module for daemon logic for parentopticon.
These are functions that run all the time.
"""
import logging

def _setup_logger() -> None:
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	logger.addHandler(logging.StreamHandler())
	
def main() -> None:
	_setup_logger()
	logging.info("Set up.")
		

