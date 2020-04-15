"""
Module for daemon logic for parentopticon.

This program runs at startup on a user session and gathers information
about running programs. It also shuts down programs when time is up and
tells the user what is going on.
"""
import argparse
import asyncio
import datetime
import logging
import socket
import time
from typing import Iterable

from parentopticon import client, log, snapshot


LOGGER = logging.getLogger(__name__)
SNAPSHOT_TIMESPAN_SECONDS = 30

def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("-H", "--host", default="http://odroid.lan", help="The host to talk to, prefixed with the scheme")
	parser.add_argument("-l", "--loop-time", default=SNAPSHOT_TIMESPAN_SECONDS, type=int, help="The time to use for each loop")
	parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
	args = parser.parse_args()

	log.setup(logging.DEBUG if args.verbose else logging.INFO)
	my_client = client.Client(args.host)
	LOGGER.info("Parentopticon daemon starting.")
	try:
		last_success = time.time()
		while True:
			start = time.time()
			try:
				my_client.snap_and_enforce(time.time() - last_success)
				last_success = time.time()
			except client.SkipLoop as ex:
				LOGGER.warning("Skipping the loop. %s", ex)
			end = time.time()
			time.sleep(args.loop_time - (end - start))
	except KeyboardInterrupt:
		LOGGER.info("Exiting due to SIGINT")
	LOGGER.info("Parentopticon daemon closed.")
