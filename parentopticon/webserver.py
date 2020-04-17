import argparse
import logging
import typing

from sanic import Sanic
from sanic.response import empty, html, json, redirect

from parentopticon import db, jinja_env, log, version
from parentopticon.db import queries, tables
from parentopticon.db.connection import Connection

LOGGER = logging.getLogger(__name__)
app = Sanic()
app.static("/static", "./static")
app.static("/favicon.ico", "static/img/parentopticon.ico")

def _render(template: str, **kwargs):
	return html(app.jinja_env.get_template(template).render(**kwargs))


@app.route("/action", methods=["GET"])
async def action_list(request):
	LOGGER.info("Getting list of actions for '%s'", request.args["hostname"])
	return json([])
	return json([{
		"type": "warn",
		"content": "Oh, it's comin down.",
	},{
		"type": "kill",
		"content": 14818,
	}])

@app.route("/config", methods=["GET"])
async def config_get(request):
	programs = list(tables.Program.list(app.db_connection))
	program_groups = list(tables.ProgramGroup.list(app.db_connection))
	program_sessions = list(tables.ProgramSession.list(app.db_connection, end=None))
	return _render("config.html",
		programs=programs,
		program_groups=program_groups,
		program_sessions=program_sessions,
	)

@app.route("/config/program/<program_id:int>", methods=["GET"])
async def config_program_get(request, program_id: int):
	program = tables.Program.get(app.db_connection, program_id)
	if not program:
		return redirect("/config/program")
	program_groups = list(tables.ProgramGroup.list(app.db_connection))
	program_processes = list(tables.ProgramProcess.list(app.db_connection, program=program_id))
	return _render("program.html",
		program_groups=program_groups,
		program=program,
		program_processes=program_processes,
	)

@app.route("/config/program", methods=["GET"])
async def config_programs_get(request):
	programs = list(tables.Program.list(app.db_connection))
	program_groups = list(tables.ProgramGroup.list(app.db_connection))
	return _render("programs.html",
		programs = programs,
		program_groups = program_groups,
	)

@app.route("/config/program", methods=["POST"])
async def config_programs_post(request):
	name = request.form["name"][0]
	program_group = int(request.form["program_group"][0])
	program_id = tables.Program.insert(app.db_connection,
		name = name,
		program_group = program_group,
	)
	return redirect("/config/program/{}".format(program_id))


@app.route("/config/program-group/<program_group_id:int>", methods=["GET"])
async def config_program_group_get(request, program_group_id: int):
	pg = tables.ProgramGroup.get(app.db_connection, program_group_id)
	if not pg:
		return redirect("/config/program-group")
	return _render("program-group.html", program_group=pg)

@app.route("/config/program-group", methods=["POST"])
async def config_program_groups_post(request):
	name = request.form["name"][0]
	minutes_monday = int(request.form["minutes_monday"][0])
	minutes_tuesday = int(request.form["minutes_tuesday"][0])
	minutes_wednesday = int(request.form["minutes_wednesday"][0])
	minutes_thursday = int(request.form["minutes_thursday"][0])
	minutes_friday = int(request.form["minutes_friday"][0])
	minutes_saturday = int(request.form["minutes_saturday"][0])
	minutes_sunday = int(request.form["minutes_sunday"][0])
	minutes_weekly = int(request.form["minutes_weekly"][0])
	minutes_monthly = int(request.form["minutes_monthly"][0])
	program_group_id = tables.ProgramGroup.insert(app.db_connection,
		name = name,
		minutes_monday = minutes_monday,
		minutes_tuesday = minutes_tuesday,
		minutes_wednesday = minutes_wednesday,
		minutes_thursday = minutes_thursday,
		minutes_friday = minutes_friday,
		minutes_saturday = minutes_saturday,
		minutes_sunday = minutes_sunday,
		minutes_weekly = minutes_weekly,
		minutes_monthly = minutes_monthly,
	)
	return redirect("/config/program-group/{}".format(program_group_id))


@app.route("/config/program-group", methods=["GET"])
async def config_program_groups_get(request):
	return _render("program-groups.html")

@app.route("/config/program-process", methods=["POST"])
async def config_program_process_post(request):
	name = request.form["name"][0]
	program = int(request.form["program"][0])
	program_process_id = tables.ProgramProcess.insert(app.db_connection,
		name = name,
		program = program,
	)
	return redirect("/config/program/{}".format(program))

@app.route("/program-by-process", methods=["GET"])
async def config_programs_get(request):
	# hostname = request.args["hostname"]
	# username = request.args["username"]
	process_by_program = queries.list_program_by_process(app.db_connection)
	return json(process_by_program)

@app.route("/snapshot", methods=["POST"])
def program_post(request):
	"Handle a client POSTing its currently running programs"
	LOGGER.info("got a snapshot POST: %s", request.json)
	elapsed_seconds = request.json.get("elapsed_seconds", 0)
	hostname = request.json["hostname"]
	username = request.json["username"]
	pid_to_program = request.json["programs"]
	queries.snapshot_store(app.db_connection, hostname, username, elapsed_seconds, pid_to_program)
	return empty()

@app.route("/")
async def root(request):
	user_to_status = queries.user_to_status(app.db_connection)
	return _render("index.html",
		user_to_status=user_to_status,
	)


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

@app.listener("after_server_start")
async def on_server_start(app, loop) -> None:
	"""Handle server start and track our background task."""
	app.db_connection = Connection()
	app.db_connection.connect()
	tables.create_all(app.db_connection)

	app.jinja_env = jinja_env.create()
	LOGGER.info("Server start hook complete")

def run() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("-H", "--host", default="0.0.0.0", help="The port/host to bind to.")
	parser.add_argument("-p", "--port", type=int, default=13598, help="The port to run on.")
	args = parser.parse_args()

	log.setup()
	try:
		LOGGER.info("Webserver starting.")
		app.run(host=args.host, port=args.port)
	except KeyboardInterrupt:
		LOGGER.info("shutting down due to SIGINT")

