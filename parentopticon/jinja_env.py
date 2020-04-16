import datetime

import arrow
import jinja2

def _humanize(t: datetime.datetime) -> str:
	return arrow.get(t).humanize() if t else "none"

def create() -> jinja2.Environment:
	env = jinja2.Environment(
		loader=jinja2.PackageLoader("parentopticon", "templates"),
		autoescape=jinja2.select_autoescape(["html", "xml"]),
	)
	env.filters["humanize"] = _humanize
	return env
