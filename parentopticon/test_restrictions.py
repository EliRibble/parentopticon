import datetime
import typing
import unittest

from parentopticon import restrictions

import yaml

# Basic limits configuration that we'll use in some
# tests where we don't really care about its content.
LIMITS_GAMES = [
	"limits:",
	"  - name: games-limits",
	"    daily: 90",
	"    weekly: 400",
	"    monthly: 0",
]

# Basic window configuration that we'll use in some
# tests where we don't really care about its content.
WINDOW_GAMES = [
	"windows:",
	"  - name: games-window",
	"    monday: [0700-1600]",
	"    tuesday: [0700-1600]",
	"    wednesday: [0700-1600]",
	"    thursday: [0700-1600]",
	"    friday: [0700-1600]",
	"    saturday: [0700-1600]",
	"    sunday: [0700-1600]",
]

def _load(content: str) -> typing.Dict[str, typing.Any]:
	return yaml.safe_load(content)

def _parse_config(content: str) -> restrictions.Config:
	data = _load(content)
	data["groups"] = data.get("groups", [])
	data["limits"] = data.get("limits", [])
	data["programs"] = data.get("programs", [])
	data["restrictions"] = data.get("restrictions", [])
	data["windows"] = data.get("windows", [])
	return restrictions._parse_entire_config(data)

class TestProgram(unittest.TestCase):
	"Test for behviors around defining programs"
	def test_simple(self):
		"Can we parse the simple list of programs?"
		config = _parse_config("\n".join([
			"programs:",
			"  - name: Minecraft",
			"  - name: Terraria",
		]))
		self.assertEqual(len(config.programs), 2)
		self.assertIn("Minecraft", config.programs)
		self.assertIn("Terraria", config.programs)
		
	def test_processes(self):
		"Can we parse programs with process names?"
		config = _parse_config("\n".join([
			"programs:",
			"  - name: Minecraft",
			"    processes:",
			"      - minecraft",
			"      - minecraft-launcher",
		]))
		self.assertEqual(len(config.programs), 1)
		self.assertEqual(len(config.programs["Minecraft"].processes), 2)

class TestGroup(unittest.TestCase):
	"Tests for behaviors around defining groups."
	def test_basic(self):
		"Can we parse just some group names?"
		config = _parse_config("\n".join([
			"groups:",
			"  - name: games",
			"  - name: browsers",
		]))
		self.assertEqual(len(config.groups), 2)

	def test_limit(self):
		"Can we tie a group to a limit pool?"
		config = _parse_config("\n".join([
			"groups:",
			"  - name: games",
			"    limits: games-limits",
		] + LIMITS_GAMES))
		self.assertEqual(config.groups["games"].limits.name, "games-limits")

	def test_bad_window(self):
		"Do we error on a window that does not exist?"
		with self.assertRaises(KeyError):
			_parse_config("\n".join([
				"groups:",
				"  - name: games",
				"    window: bad-window-name",
			] + WINDOW_GAMES))

	def test_window(self):
		"Can we tie a group to a restriction window?"
		config = _parse_config("\n".join([
			"groups:",
			"  - name: games",
			"    window: games-window",
		] + WINDOW_GAMES))
		self.assertEqual(config.groups["games"].window.name, "games-window")


class TestWindow(unittest.TestCase):
	"Tests for behavior parsing windows."
	def test_basic(self):
		"Can we parse a simple window?"
		config = _parse_config("\n".join([
			"windows:",
			"  - name: games-window",
			"    monday: [0700-1600]",
			"    tuesday: [0700-1600]",
			"    wednesday: [0700-1600]",
			"    thursday: [0700-1600]",
			"    friday: [0700-1600]",
			"    saturday: [0700-1600]",
			"    sunday: [0700-1600]",
		]))
		self.assertEqual(len(config.windows), 1)
		games_window = config.windows["games-window"]
		self.assertTrue(games_window.monday.is_locked(
			datetime.time(6)))
		self.assertFalse(games_window.tuesday.is_locked(
			datetime.time(8)))

	def test_complex_windows(self):
		"Can we parse a window with different intervals?"
		config = _parse_config("\n".join([
			"windows:",
			"  - name: games-window",
			"    monday: [0700-0830, 13-17]",
			"    tuesday: [5-8, 20-2010]",
			"    wednesday: []",
			"    thursday: []",
			"    friday: []",
			"    saturday: []",
			"    sunday: []",
		]))
		self.assertEqual(len(config.windows), 1)
		games_window = config.windows["games-window"]
		self.assertTrue(games_window.monday.is_locked(datetime.time(6)))
		self.assertFalse(games_window.monday.is_locked(datetime.time(7, 15)))
		self.assertTrue(games_window.monday.is_locked(datetime.time(12)))
		self.assertFalse(games_window.monday.is_locked(datetime.time(16, 59)))
		self.assertTrue(games_window.tuesday.is_locked(datetime.time(4)))
		self.assertFalse(games_window.tuesday.is_locked(datetime.time(6)))
		self.assertTrue(games_window.tuesday.is_locked(datetime.time(9)))
		self.assertFalse(games_window.tuesday.is_locked(datetime.time(20, 5)))
		self.assertTrue(games_window.tuesday.is_locked(datetime.time(20, 10)))
		self.assertTrue(games_window.wednesday.is_locked(datetime.time(3)))
		
class TestTime(unittest.TestCase):
	def test_long(self):
		"Can we parse time like 0730?"
		t = restrictions._parse_time("0730")
		self.assertEqual(t.hour, 7)
		self.assertEqual(t.minute, 30)

	def test_short(self):
		"Can we parse time like '07'?"
		t = restrictions._parse_time("07")
		self.assertEqual(t.hour, 7)
		self.assertEqual(t.minute, 0)

