#!/usr/bin/python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import argparse
import socket
import getpass

import messaging
import boxtest
import boxportdistrib
import boxconfig

import boxclient

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("board_type", help="type of board to test (ex: rpi3)")
parser.add_argument("-i", "--interactive", help="interactive testing, decide waiting time manually", action="store_true")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
args = parser.parse_args()

# argument variables
interactive = args.interactive
board_type = args.board_type
verbose = args.verbose

# load config
config = boxconfig.BoxConfig()

# colored output
OKGREEN = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'
SUCCESS = OKGREEN + "SUCCESS" + ENDC
FAILED = FAIL + "FAILED" + ENDC


# run test sequence
failed = False

assert board_type == "rpi2" or board_type == "rpi3"
with boxclient.BoxClient("localhost", boxportdistrib.get_port_box_server(), board_type) as boxc:
	print(f"connected to board: {(boxc.board_idx, boxc.board_id)}")

	boxc.board_start()

	print("=" * 20)
	# wait for network boot
	# TODO: have the try comm check the output of the comm and timeout after 20s
	if boxtest.tryComm(verbose, config.get_boxpath("."), interactive, board_id, board_type, 20):
		print(SUCCESS + ": Comm")
	else:
		print(FAILED + ": Comm")
		failed = True

	print("=" * 20)
	if boxtest.tryOpenOcd(verbose, config.get_boxpath("."), interactive, board_id, 5):
		print(SUCCESS + ": OpenOCD")
	else:
		print(FAILED + ": OpenOCD")
		failed = True

	print("=" * 20)
	print("done")


print("=" * 20)
if failed:
	print(FAILED)
	exit(-2)
else:
	print(SUCCESS)
	exit(0)


