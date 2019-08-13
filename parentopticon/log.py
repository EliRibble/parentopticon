"""
Module for logging functions.
"""
import logging
import logging.handlers
import os
import typing

def _xdg_data_home() -> typing.Text:
	return os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

def setup() -> None:
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	stream_handler = logging.StreamHandler()
	stream_handler.setFormatter(formatter)
	file_handler = logging.handlers.RotatingFileHandler(
		filename=os.path.join(_xdg_data_home(), "parentopticon.log"),
		mode="a",
		maxBytes=1024*1024*10,
		backupCount=10,
	)
	file_handler.setFormatter(formatter)
	logger.addHandler(stream_handler)
	logger.addHandler(file_handler)
