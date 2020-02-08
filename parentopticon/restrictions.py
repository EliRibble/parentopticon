"""This module contains functions for reading in configured restrictoins."""
import datetime
import enum
import typing

import yaml

class Window:
	"""A window of time between unlock and lock."""
	def __init__(self, start: datetime.time, end: datetime.time):
		self.end = end
		self.start = start

	def is_locked(self, when: datetime.time):
		return when < self.start or self.end <= when

class WindowSet:
	"""A group of window sets to apply together."""
	def __init__(self, windows: typing.Iterable[Window]):
		self.windows = sorted(windows, key=lambda w: w.start)

	def is_locked(self, when: datetime.time):
		for window in self.windows:
			if not window.is_locked(when):
				return False
		return True


class WindowWeek:
	"""The windows applied every week."""
	def __init__(self,
		name: str,
		monday: WindowSet,
		tuesday: WindowSet,
		wednesday: WindowSet,
		thursday: WindowSet,
		friday: WindowSet,
		saturday: WindowSet,
		sunday: WindowSet):
		"""A grouping of windows for a restriction."""
		self.name = name
		self.monday = monday
		self.tuesday = tuesday
		self.wednesday = wednesday
		self.thursday = thursday
		self.friday = friday
		self.saturday = saturday
		self.sunday = sunday


class LimitSet:
	"""A group of limits that form a pool."""
	def __init__(self,
		name: str,
		daily: typing.Optional[int],
		hourly: typing.Optional[int],
		monthly: typing.Optional[int],
		weekly: typing.Optional[int]):
		self.name = name
		self.daily = daily
		self.hourly = hourly
		self.monthly = monthly
		self.weekly = weekly


class Program:
	"""Information about a single program we are tracking."""
	def __init__(self, name: str, processes: typing.List[str]):
		self.name = name
		self.processes = processes


class Group:
	"""A group of programs with the same restrictions."""
	def __init__(self,
		name: str,
		limits: typing.Optional[LimitSet] = None,
		window: typing.Optional[WindowWeek] = None):
		self.name = name
		self.limits = limits
		self.window = window


class Config:
	"""A full configuration with various restrictions."""
	def __init__(self,
		groups: typing.List[Group],
		programs: typing.List[Program],
		windows: typing.List[WindowWeek]):
		self.groups = {group.name: group for group in groups}
		self.programs = {program.name: program for program in programs}
		self.windows = {window.name: window for window in windows}


def load() -> Config:
	"""Read in the system-wide restrictions."""
	with open("/etc/parentopticon.yaml", "r") as config:
		content = yaml.load(config)
	return _parse_entire_config(content)

def _parse_entire_config(content: typing.Dict) -> Config:
	"""Take a config which is just a JSON body and turn it into the proper instances."""
	limits = [_parse_limitset(l) for l in content["limits"]]
	windows = [_parse_window_week(w) for w in content["windows"]]
	groups = [_parse_group(g, limits, windows) for g in content["groups"]]
	programs = [_parse_program(p) for p in content["programs"]]
	return Config(groups, programs, windows)

def _parse_group(
	content: typing.Dict[str, typing.Any],
	limits: typing.List[LimitSet],
	windows: typing.List[WindowWeek]) -> Group:
	"""Create a group from the provided config data structure."""
	limit_name = content.get("limits")
	limit = {l.name: l for l in limits}[limit_name] if limit_name else None
	window_name = content.get("window")
	window = {w.name: w for w in windows}[window_name] if window_name else None
	return Group(
		name = content["name"],
		limits = limit if limit else None,
		window = window if window else None,
	)


def _parse_limitset(content: typing.Dict[str, typing.Any]) -> LimitSet:
	"""Take a dict of data and turn it into a list of Limits."""
	daily = content.get("daily")
	hourly = content.get("hourly")
	monthly = content.get("monthly")
	weekly = content.get("weekly")
	return LimitSet(
		name = content["name"],
		daily = daily,
		hourly = hourly,
		monthly = monthly,
		weekly = weekly,
	)

def _parse_program(content: typing.Dict[str, typing.Any]) -> Program:
	"""Parse a single program from a config file."""
	return Program(
		name = content["name"],
		processes = content.get("processes", []),
	)
	

def _parse_time(t: str) -> datetime.time:
	"Parse a string like 0735 into a time."
	if len(t) <= 2:
		return datetime.time(hour=int(t))
	elif len(t) == 4:
		return datetime.time(hour=int(t[:2]), minute=int(t[2:]))
	else:
		raise ValueError("Can't parse '{}' as a time".format(t))


def _parse_window_week(content: typing.Dict[str, typing.Any]) -> WindowWeek:
	return WindowWeek(
		name      = content["name"],
		monday    = _parse_windowset(content["monday"]),
		tuesday   = _parse_windowset(content["tuesday"]),
		wednesday = _parse_windowset(content["wednesday"]),
		thursday  = _parse_windowset(content["thursday"]),
		friday    = _parse_windowset(content["friday"]),
		saturday  = _parse_windowset(content["saturday"]),
		sunday    = _parse_windowset(content["sunday"]),
	)


def _parse_window(content: str) -> Window:
	"Create a window from a string."
	start, _, end = content.partition("-")
	return Window(
		start = _parse_time(start),
		end = _parse_time(end),
	)


def _parse_windowset(content: typing.Dict[str, typing.List[str]]) -> WindowSet:
	windows = [_parse_window(w) for w in content]
	return WindowSet(windows)
