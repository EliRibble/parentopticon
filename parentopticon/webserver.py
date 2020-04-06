import logging
import typing

from sanic import Sanic
from sanic.response import empty, html, json, redirect

from parentopticon import db, log, version

LOGGER = logging.getLogger(__name__)
app = Sanic()


def _render(template: str, **kwargs):
	return html(app.jinja_env.get_template(template).render(**kwargs))


@app.route("/")
async def root(request):
	limits = db.ProgramGroupLimit.list(app.db_connection)
	window_weeks = app.db_connection.window_week_list()
	groups = app.db_connection.group_list()
	programs = app.db_connection.program_list()
	program_sessions = app.db_connection.program_session_list_open()
	return _render("index.html",
		groups=list(groups),
		limits=list(limits),
		program_sessions=program_sessions,
		programs=programs,
		window_weeks=list(window_weeks),
	)


@app.route("/action", methods=["GET"])
async def action_list(request):
	LOGGER.info("Getting list of actions for '%s'", request.args["hostname"])
	return json([{
		"type": "warn",
		"content": "Oh, it's comin down.",
	},{
		"type": "kill",
		"content": 14818,
	}])

@app.route("/group", methods=["POST"])
async def group_post(request):
	name = request.form["name"][0]
	limit = int(request.form["limit"][0])
	window_week = int(request.form["window_week"][0])
	limit = None if limit == -1 else limit
	window_week = None if window_week == -1 else window_week
	group_id = app.db_connection.group_create(
		name = name,
		limit = limit,
		window_week = window_week,
	)
	return redirect("/group/{}".format(group_id))


@app.route("/group/<group_id:int>", methods=["GET"])
async def group_get(request, group_id: int):
	group = app.db_connection.group_get(group_id)
	return _render("group.html", group=group)

@app.route("/limit", methods=["POST"])
async def limit_post(request):
	name = request.form["name"][0]
	daily = int(request.form["daily"][0])
	weekly = int(request.form["weekly"][0])
	monthly = int(request.form["monthly"][0])
	limit_id = app.db_connection.limit_create(
		name = name,
		daily = daily,
		weekly = weekly,
		monthly = monthly,
	)
	return redirect("/limit/{}".format(limit_id))

@app.route("/limit/<limit_id:int>", methods=["GET"])
async def limit_get(request, limit_id: int):
	limit = app.db_connection.limit_get(limit_id)
	return _render("limit.html", limit=limit)

@app.route("/program/<program_id:int>", methods=["GET"])
async def program(request, program_id: int):
	program = app.db_connection.program_get(program_id)
	program_sessions = app.db_connection.program_session_list_by_program(program_id)
	return _render("program.html", program=program, program_sessions=program_sessions)

@app.route("/program", methods=["GET"])
def program_list(request):
	return json({
		"net.minecraft.client.main.Main": "Minecraft",
		"minecraft-launcher": "Minecraft",
	})

@app.route("/program", methods=["POST"])
async def program_post(request):
	name = request.form["name"][0]
	group = int(request.form["group"][0])
	program_id = app.db_connection.program_create(
		name = name,
		group = group,
	)
	processes_str = request.form["processes"][0]
	if processes_str:
		for process in processes_str.split(","):
			process = process.strip()
			app.db_connection.process_create(
				name = process,
				program = program_id,
			)
	return redirect("/program/{}".format(program_id))


@app.route("/snapshot", methods=["POST"])
def program_post(request):
	LOGGER.info("got a snapshot POST: %s", request.json)
	return empty()

@app.route("/window", methods=["POST"])
async def window_post(request):
	name = request.form["name"][0]
	monday = request.form["monday"][0]
	tuesday = request.form["tuesday"][0]
	wednesday = request.form["wednesday"][0]
	thursday = request.form["thursday"][0]
	friday = request.form["friday"][0]
	saturday = request.form["saturday"][0]
	sunday = request.form["sunday"][0]
	window_id = app.db_connection.window_week_create(
		name = name,
	)
	for index, day in enumerate(("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")):
		content = request.form[day][0]
		for part in content.split(","):
			start_str, _, end_str = part.partition("-")
			start = int(start_str)
			end = int(end_str)
			app.db_connection.window_week_day_span_create(index, end, start, window_id)
	return redirect("/window/{}".format(window_id))

@app.route("/window/<window_id:int>", methods=["GET"])
async def window_get(request, window_id: int):
	window = app.db_connection.window_week_get(window_id)
	return _render("window.html", window=window)

def run() -> None:
	log.setup()
	try:
		LOGGER.info("Webserver starting.")
		app.run(host="127.0.0.1", port=13598)
	except KeyboardInterrupt:
		LOGGER.info("shutting down due to SIGINT")

