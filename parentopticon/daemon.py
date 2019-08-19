"""
Module for daemon logic for parentopticon.
These are functions that run all the time.
"""
import logging
import time

import parentopticon.log
import parentopticon.snapshot

def _do_loop() -> None:
	parentopticon.snapshot.take()

def main() -> None:
	parentopticon.log.setup()
	logging.info("Daemon started.")
	try:
		while True:
			_do_loop()
			time.sleep(60)
	except KeyboardInterrupt:
		logging.info("Shutting down due to received SIGINT")
