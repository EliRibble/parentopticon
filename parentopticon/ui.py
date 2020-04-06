import subprocess

def show_alert(title: str, content: str) -> None:
	"""Show an alert message using the desktop notifier."""
	subprocess.call(["notify-send", title, content])
