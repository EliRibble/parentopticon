"""This module creates a Pythonic interface to cn_proc.

cn_proc is a small C program for interfacing with the Linux kernel and getting
events around process creation.
"""
import asyncio
import collections
import logging
import re
import subprocess

LOGGER = logging.getLogger(__name__)

Event = collections.namedtuple("Event", (
	"cmd",
	"pid",
	"tgid",
	"type",
))

EVENT_PATTERN = re.compile(r"event: (?P<type>exec|fork|none|uid|gid|sid|exit) (?P<pid>\d+) (?P<tgid>\d+): (?P<cmd>.*)")

async def events():
	"Get an iterator of events in the system related to processes."
	cmd = "bin/cn_proc"
	# cmd = "bin/outputer"
	process = await asyncio.create_subprocess_shell(
		cmd,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE)
	LOGGER.debug("Started '%s'", cmd)
	while process.returncode is None:
		LOGGER.debug("Waiting for data on stdout")
		data = await process.stdout.readline()
		line = data.decode("utf-8").rstrip()
		LOGGER.debug("Got a line: '%s'", line)
		match = EVENT_PATTERN.match(line)
		if not match:
			raise ValueError("Not a valid line: '{}'".format(line))
		yield Event(**match.groupdict())
