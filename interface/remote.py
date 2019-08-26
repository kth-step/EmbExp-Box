#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import argparse
import logging

import embexpremote
import boxclient

env_var_ssh_port = "EMBEXP_REMOTE_PORT"
env_var_ssh_host = "EMBEXP_REMOTE_HOST"

# TODO: change this to use the networks.json file
if (env_var_ssh_port in os.environ) and (env_var_ssh_host in os.environ):
	ssh_port = os.environ[env_var_ssh_port]
	ssh_host = os.environ[env_var_ssh_host]
else:
	raise Exception("the environment variables for the server are not configured")


# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("board_type", help="type of the board to obtain")

parser.add_argument("-idx", "--instance_idx", help="instance index", type=int)

parser.add_argument("--box_name", help="name of the box to connect to")
parser.add_argument("--board_name", help="name of the board to connect to")

parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
args = parser.parse_args()

# set log level
if args.verbose:
	logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
else:
	logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

# argument variables
board_type  = args.board_type
instance_idx = 0 if args.instance_idx == None else args.instance_idx
box_name = args.box_name
board_name = args.board_name
logging.info(f"board_type = {board_type}")
logging.info(f"instance_idx = {instance_idx}")
logging.info(f"box_name = {box_name}")
logging.info(f"board_name = {board_name}")


if instance_idx != None and (instance_idx < 0 or 99 < instance_idx):
	raise Exception("instance index is not usable (out of range)")


OKBLUE = '\033[94m'
ENDC = '\033[0m'


try:
	with embexpremote.EmbexpRemote(instance_idx, ssh_host, ssh_port, board_type, box_name, board_name) as remote:
		remote.startup()

		print(OKBLUE)
		print("===============================")
		print("===    finished starting    ===")
		print("===============================")
		print(ENDC)

		print("press enter to shut down.")
		sys.stdout.flush()
		input()
except boxclient.BoxServerNoBoardException as e:
	print(20*"=")
	print(f"could not get board, because: {e}")
	exit(-1)



