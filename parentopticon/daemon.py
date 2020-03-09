"""
Module for daemon logic for parentopticon.
These are functions that run all the time.
"""
import asyncio
import datetime
import logging
import time

from parentopticon import db, enforcement, log, restrictions, snapshot
from parentopticon.webserver import app

import arrow
import jinja2


SNAPSHOT_TIMESPAN_SECONDS = 10
async def _snapshot_loop(stop_event: asyncio.Event, db_connection: db.Connection) -> None:
	"""Perform the regular snapsots of what's running."""
	logging.info("Started loop to take snapshots.")
	while not stop_event.is_set():
		snapshot.take(db_connection, SNAPSHOT_TIMESPAN_SECONDS)
		enforcement.go(db_connection)
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
	app.jinja_env.filters["humanize"] = _humanize
	app.jinja_env.filters["timespan"] = _timespan


def _humanize(t: datetime.datetime) -> str:
	return arrow.get(t).humanize() if t else "none"

def _timespan(t: datetime.timedelta) -> str:
	s = t.total_seconds()
	if s < 10:
		return "few seconds"
	elif s < 100:
		return "{} seconds".format(s)
	elif s < 1000:
		return "few minutes"
	elif s < (60 * 60 * 100):
		return "{} minutes".format(s / 60)
	elif s < (60 * 60 * 30):
		return "{} hours".format(s / (60 * 60))
	elif s < (60 * 60 * 24 * 400):
		return "{} days".format(s / (60 * 60 * 24))
	else:
		return "{} years".format(s / (60 * 60 * 24 * 365))

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

