"""
Module for daemon logic for parentopticon.
These are functions that run all the time.
"""
import asyncio
import logging
import time

from parentopticon import db, log, restrictions, snapshot
from parentopticon.webserver import app

import jinja2


SNAPSHOT_TIMESPAN_SECONDS = 10
async def _snapshot_loop(stop_event: asyncio.Event, db_connection: db.Connection) -> None:
	"""Perform the regular snapsots of what's running."""
	logging.info("Started loop to take snapshots.")
	while not stop_event.is_set():
		shot = snapshot.take(db_connection, SNAPSHOT_TIMESPAN_SECONDS)
		try:
			await asyncio.wait_for(stop_event.wait(), SNAPSHOT_TIMESPAN_SECONDS)
		except asyncio.TimeoutError:
			pass
	logging.info("Snapshot loop closed")


@app.listener("after_server_start")
async def on_server_start(app, loop) -> None:
	"""Handle server start and track our background task."""
	app.db_connection = db.Connection()
	app.db_connection.connect()
	app.stop_event = asyncio.Event()
	app.snapshot_task = loop.create_task(_snapshot_loop(app.stop_event, app.db_connection))
	app.jinja_env = jinja2.Environment(
		loader=jinja2.PackageLoader("parentopticon", "templates"),
		autoescape=jinja2.select_autoescape(["html", "xml"]),
	)

@app.listener("before_server_stop")
async def on_server_stop(app, loop) -> None:
	app.stop_event.set()
	await app.snapshot_task

def main() -> None:
	log.setup()
	try:
		logging.info("Daemon starting.")
		app.run(host="127.0.0.1", port=13598)
		logging.info("Ending prematurely.")
	except KeyboardInterrupt:
		logging.info("Shutting down due to received SIGINT")
		end_event.set()

