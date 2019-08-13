"""
Module for daemon logic for parentopticon.
These are functions that run all the time.
"""
import logging

import parentopticon.log

def main() -> None:
	parentopticon.log.setup()
	logging.info("Set up.")
		

