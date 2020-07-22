import argparse
import datetime
import logging
import typing

import flask
import flask_login

import toml

from sanic import Sanic
from sanic.response import empty, html, json, redirect, text

from parentopticon import db, jinja_env, log, version
from parentopticon.db import queries, tables
from parentopticon.db.connection import Connection

LOGGER = logging.getLogger(__name__)

flask_app = flask.Flask("parentopticon")
login_manager = flask_login.LoginManager()

app = Sanic()
app.static("/static", "./static")
app.static("/favicon.ico", "static/img/parentopticon.ico")

def _render(filename: str, **kwargs):
	template = app.jinja_env.get_template(filename)
	content = template.render(now=datetime.datetime.now(), **kwargs)
	return html(content)


@app.route("/action", methods=["GET"])
async def action_list(request):
	hostname = request.args["hostname"][0]
	username = request.args["username"][0]
	actions = queries.actions_for_username(app.db_connection, hostname, username)
	return json([{
		"content": action.content,
		"type": action.type,
	} for action in actions])

@app.route("/config", methods=["GET"])
async def config_get(request):
	programs = list(tables.Program.list(app.db_connection))
	program_groups = list(tables.ProgramGroup.list(app.db_connection))
	program_sessions = sorted(
		tables.ProgramSession.list(app.db_connection),
		key=lambda s: s.start,
		reverse=True,
	)
	website_visits = sorted(
		tables.WebsiteVisit.list(app.db_connection),
		key=lambda s: s.at,
		reverse=True,
	)
	return _render("config/index.html",
		programs=programs,
		program_groups=program_groups,
		program_sessions=program_sessions,
		website_visits=website_visits,
	)

@app.route("/config/one-time-message", methods=["GET"])
async def config_one_time_messages_get(request):
	usernames = queries.usernames(app.db_connection)
	one_time_messages = tables.OneTimeMessage.list(app.db_connection)
	return _render("config/one-time-messages.html",
		one_time_messages = one_time_messages,
		usernames=usernames
	)

@app.route("/config/one-time-message", methods=["POST"])
async def config_one_time_message_post(request):
	content = request.form["content"][0]
	username = request.form["username"][0]
	program_id = tables.OneTimeMessage.insert(app.db_connection,
		content = content,
		hostname = None,
		created = datetime.datetime.now(),
		sent = None,
		username = username,
	)
	return redirect("one-time-message")

@app.route("/config/program/<program_id:int>", methods=["GET"])
async def config_program_get(request, program_id: int):
	program = tables.Program.get(app.db_connection, program_id)
	if not program:
		return redirect("program")
	program_groups = list(tables.ProgramGroup.list(app.db_connection))
	program_processes = list(tables.ProgramProcess.list(app.db_connection, program=program_id))
	return _render("config/program.html",
		program_groups=program_groups,
		program=program,
		program_processes=program_processes,
	)

@app.route("/config/program", methods=["GET"])
async def config_programs_get(request):
	programs = list(tables.Program.list(app.db_connection))
	program_groups = list(tables.ProgramGroup.list(app.db_connection))
	return _render("config/programs.html",
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
	return redirect("program/{}".format(program_id))


@app.route("/config/program-group/<program_group_id:int>", methods=["GET"])
async def config_program_group_get(request, program_group_id: int):
	pg = tables.ProgramGroup.get(app.db_connection, program_group_id)
	if not pg:
		return redirect("..")
	user_to_usage = queries.user_to_usage(app.db_connection, program_group=pg)
	return _render("config/program-group.html",
		program_group=pg,
		user_to_usage=user_to_usage,
	)
@app.route("/config/program-group/<program_group_id:int>", methods=["POST"])
async def config_program_group_put(request, program_group_id: int):
	values = {
		"name": request.form["name"][0],
		"minutes_monday": request.form["minutes_monday"][0],
		"minutes_tuesday": request.form["minutes_tuesday"][0],
		"minutes_wednesday": request.form["minutes_wednesday"][0],
		"minutes_thursday": request.form["minutes_thursday"][0],
		"minutes_friday": request.form["minutes_friday"][0],
		"minutes_saturday": request.form["minutes_saturday"][0],
		"minutes_sunday": request.form["minutes_sunday"][0],
		"minutes_weekly": request.form["minutes_weekly"][0],
		"minutes_monthly": request.form["minutes_monthly"][0],
	}
	LOGGER.info("Updating program-group %d to %s", program_group_id, values)
	pg = tables.ProgramGroup.get(app.db_connection, program_group_id)
	if not pg:
		return redirect("..")
	tables.ProgramGroup.update(
		app.db_connection,
		program_group_id,
		**values,
	)
	return redirect("../program-group/{}".format(program_group_id))

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
	return redirect("program-group/{}".format(program_group_id))


@app.route("/config/program-group", methods=["GET"])
async def config_program_groups_get(request):
	return _render("config/program-groups.html")

@app.route("/config/program-process", methods=["POST"])
async def config_program_process_post(request):
	name = request.form["name"][0]
	program = int(request.form["program"][0])
	program_process_id = tables.ProgramProcess.insert(app.db_connection,
		name = name,
		program = program,
	)
	return redirect("program/{}".format(program))

@app.route("/denied", methods=["GET"])
async def denied_get(request):
	"Tell a client its not allowed to go there."
	url = request.args.get("url", "unknown")
	return text("You've attempted to access '{}', which is denied.".format(url))

@app.route("/program-by-process", methods=["GET"])
async def config_programs_get(request):
	# hostname = request.args["hostname"]
	# username = request.args["username"]
	process_by_program = queries.list_program_by_process(app.db_connection)
	return json(process_by_program)

@app.route("/program-group/<program_group_id:int>", methods=["GET"])
async def program_group_get(request, program_group_id: int):
	program_group = tables.ProgramGroup.get(app.db_connection, program_group_id)
	if not program_group:
		redirect("../..")
	user_to_usage = queries.user_to_usage(app.db_connection, program_group=program_group)
	return _render("program-group.html",
		program_group=program_group,
		user_to_usage=user_to_usage,
	)

@app.route("/")
async def root(request):
	user_to_status = queries.user_to_status(app.db_connection)
	return _render("index.html",
		user_to_status=user_to_status,
	)


@app.route("/snapshot", methods=["POST"])
async def snapshot_post(request):
	"Handle a client POSTing its currently running programs"
	LOGGER.info("got a snapshot POST: %s", request.json)
	elapsed_seconds = request.json.get("elapsed_seconds", 0)
	hostname = request.json["hostname"]
	username = request.json["username"]
	pid_to_program = request.json["programs"]
	queries.snapshot_store(app.db_connection, hostname, username, elapsed_seconds, pid_to_program)
	return empty()

@app.route("/user/<username>", methods=["GET"])
async def user(request, username: str):
	programs = list(tables.Program.list(app.db_connection))
	program_id_to_name = {program.id: program.name for program in programs}
	sessions = queries.program_session_list_since(
		connection=app.db_connection,
		moment=queries.today_start(),
		programs=None,
		username=username,
	)
	display_sessions = [{
		"end": session.end,
		"program": session.program,
		"program_name": program_id_to_name[session.program],
		"start": session.start,
		"username": session.username,
	} for session in sessions]
	return _render("user.html",
		sessions=sorted(display_sessions, key=lambda s: s["start"]),
		username=username,
	)

@app.route("/website", methods=["POST"])
async def website_post(request):
	"Handle a client POSTing a website it visits"
	tables.WebsiteVisit.insert(
		app.db_connection,
		at=datetime.datetime.now(),
		hostname=request.json["hostname"],
		incognito=request.json["incognito"],
		url=request.json["url"],
		username=request.json["username"],
	)
	if "github" in request.json["url"]:
		return text("Parentopticon says no", status=499)
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
	return redirect("window/{}".format(window_id))

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

@flask_app.route("/")
def root():
	return flask.render_template("root.html")

class User():
	"A user. Duh."
	def __init__(self) -> None:
		self.is_active = True
		self.is_authenticated = True
		self.is_anonymous = False

	def get_id() -> str:
		return "1"
		
@login_manager.user_loader
def load_user(user_id: str) -> User:
	return None

def run() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--config", default="/etc/parentopticon.toml", help="The config file to load.")
	parser.add_argument("-H", "--host", default="0.0.0.0", help="The port/host to bind to.")
	parser.add_argument("-p", "--port", type=int, default=13598, help="The port to run on.")
	parser.add_argument("--verbose", action="store_true", help="Use verbose logging.")
	args = parser.parse_args()

	log.setup(level=logging.DEBUG if args.verbose else logging.INFO)
	try:
		configuration = toml.load(args.config)
	except FileNotFoundError:
		configuration = {
			"secret_key": "this-is-not-secret-don't-use-this",
		}
	try:
		LOGGER.info("Webserver starting.")
		login_manager.init_app(flask_app)
		flask_app.secret_key = configuration["secret_key"]
		flask_app.run(host=args.host, port=args.port)
	except KeyboardInterrupt:
		LOGGER.info("shutting down due to SIGINT")

