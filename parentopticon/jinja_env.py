import datetime
import logging
import sys

import arrow
import jinja2

LOGGER = logging.getLogger(__name__)

def _humanize(t: datetime.datetime) -> str:
	return arrow.get(t).humanize() if t else "none"

def _nicetime(t: datetime.datetime) -> str:
	"Turn a time display into a nice display based on today."
	now = datetime.datetime.now()
	today = now.replace(hour=0, minute=0, second=0, microsecond=0)
	diff = now - t
	if t.replace(hour=0, minute=0, second=0, microsecond=0) == today:
		return t.strftime("%H:%M")
	elif diff.days < 7:
		return t.strftime("%a %H:%M")
	elif diff.days < 365:
		return t.strftime("%a %b %d %H:%M")
	else:
		return t.isoformat()

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


class JinjaEnvironmentSanic(jinja2.Environment):
	"""A special jinja2 environment that avoids crashing sanic."""
	def handle_exception(self, source=None):
		if source is None:
			exc_type, exc_value, tb = sys.exc_info()
		else:
			exc_type = type(source)
			exc_value = source
		LOGGER.error("Jinja exception: %s %s", exc_type, exc_value)
		
def create() -> jinja2.Environment:
	env = JinjaEnvironmentSanic(
		loader=jinja2.PackageLoader("parentopticon", "templates"),
		autoescape=jinja2.select_autoescape(["html", "xml"]),
	)
	env.filters["humanize"] = _humanize
	env.filters["nicetime"] = _nicetime
	env.filters["timespan"] = _timespan
	return env
