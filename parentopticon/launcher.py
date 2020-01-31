import argparse
import logging
import subprocess

import parentopticon.log

LOGGER = logging.getLogger(__name__)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("name", help="The friendly name of the program.")
	parser.add_argument("target", help="The program to ultimately launch if the kids are good.")
	parser.add_argument("arguments", nargs="*", help="Additional arguments for the target")
	args = parser.parse_args()
	parentopticon.log.setup()

	LOGGER.info("Launching %s using '%s%s'",
		args.name,
		args.target,
		" " + " ".join(args.arguments) if args.arguments else "")
	subprocess.call([args.target] + args.arguments)
	LOGGER.info("%s Complete.", args.name)
