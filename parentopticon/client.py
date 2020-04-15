"""
Module for handling enforcement logic.
"""
import datetime
from enum import Enum
import logging
import os
import signal
import socket
from typing import Iterable, Mapping, Optional
import urllib.parse

import requests

from parentopticon import db, snapshot, ui

LOGGER = logging.getLogger(__name__)

class ActionType(Enum):
	# Kill a program
	kill = "kill"
	# Show a warning
	warn = "warn"


class SkipLoop(Exception):
	"An exception happened, we need to skip the loop."


class Action:
	def __init__(self, type_: ActionType, content: str) -> None:
		self.content = content
		self.type = type_

class Client:
	"The daemon's parentopticon client."
	def __init__(self, host: str) -> None:
		self.host = host
		self.hostname = socket.gethostname()

	def get_actions(self) -> Iterable[Action]:
		"Get the enforcement actions to take."
		url = self.url("/action", {"hostname": self.hostname})
		response = requests.get(url)
		if not response.ok:
			raise SkipLoop("Failed to get actions: %s", response.text)
		data = response.json()
		LOGGER.debug("Received actions: %s", data)
		return [Action(
			content=d["content"],
			type_=ActionType(d["type"]))
			for d in data]

	def get_processes_and_programs(self) -> Mapping[str, str]:
		"Get the processes and programs we care about."
		url = self.url("/program", {"hostname": self.hostname})
		response = requests.get(url)
		if not response.ok:
			raise SkipLoop("Failed to get interesting processes and programs: {}.".format(response.text))
		return response.json()

	def post_programs(self, pid_to_program: Mapping[int, str], elapsed_seconds: int) -> None:
		"Send the programs that have been running."
		url = self.url("/snapshot")
		data = {
			"elapsed_seconds": elapsed_seconds,
			"hostname": self.hostname,
			"programs": pid_to_program,
		}
		response = requests.post(url, json=data)
		if not response.ok:
			raise SkipLoop("Failed to send snapshot: {}".format(response.text))

	def snap_and_enforce(self, elapsed_seconds: int) -> None:
		"Get a snapshot, enforce limits."
		try:
			process_to_programs = self.get_processes_and_programs()
			pid_to_program = snapshot.take(process_to_programs)
			self.post_programs(pid_to_program, elapsed_seconds)
			actions = self.get_actions()
			for action in actions:
				do(action)
		except requests.exceptions.ConnectionError as ex:
			raise SkipLoop("Looks like the remote host isn't responding: {}".format(ex))

	def url(self, path: str, queryargs: Optional[Mapping[str, str]] = None) -> str:
		if queryargs:
			query = urllib.parse.urlencode(queryargs)
		else:
			query = ""
		return "{}{}?{}".format(
			self.host,
			path,
			query,
		)


def do(action: Action) -> None:
	"Do whatever the action says to do."
	if action.type == ActionType.kill:
		os.kill(int(action.content), signal.SIGINT)
	elif action.type == ActionType.warn:
		ui.show_alert("Thus saith dad", action.content)
	else:
		raise Exception("This should never happen.")
