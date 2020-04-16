import datetime

import arrow
import jinja2

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


def create() -> jinja2.Environment:
	env = jinja2.Environment(
		loader=jinja2.PackageLoader("parentopticon", "templates"),
		autoescape=jinja2.select_autoescape(["html", "xml"]),
	)
	env.filters["humanize"] = _humanize
	env.filters["timespan"] = _timespan
	return env
