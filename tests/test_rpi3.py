#!/usr/bin/python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import argparse
import socket
import getpass

import messaging
import boxtest

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--interactive", help="interactive testing, decide waiting time manually", action="store_true")
args = parser.parse_args()

# argument variables
interactive = args.interactive

# load config
config = boxconfig.BoxConfig()

# run test sequence
failed = False
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sc:
	sc.connect(('localhost',35555))

	# 0. select request
	request_type = "get_board"
	user_id = getpass.getuser()
	request = [request_type, user_id]
	print(messaging.recv_message(sc))
	messaging.send_message(sc, request)

	# 1. available board types
	print(messaging.recv_message(sc))

	# 2a. select type
	messaging.send_message(sc, "RPi3")

	# 2b. available boards for the selected type
	print(messaging.recv_message(sc))

	# 2c. select board
	board_id_index = -1
	messaging.send_message(sc, board_id_index)

	# 3. receive board id or error
	(board_idx, board_id, msg) = messaging.recv_message(sc)
	print(f"idx={board_idx}, id={board_id}, msg={msg}")

	if board_idx < 0:
		print("no board available or error while initializing board")
		exit(-1)

	print("=" * 20)
	# 4. receive commands
	print(messaging.recv_message(sc))
	# 5. start board
	messaging.send_message(sc, "start")

	print("=" * 20)
	# wait for network boot
	if tryCommRpi3(config.get_boxpath("."), interactive, board_id, 15):
		print("SUCCESS: Comm")
	else:
		print("FAILED: Comm")
		failed = True

	print("=" * 20)
	if tryOpenOcd(config.get_boxpath("."), interactive, board_id, 5):
		print("SUCCESS: OpenOCD")
	else:
		print("FAILED: OpenOCD")
		failed = True

	print("=" * 20)
	print("done")


print("=" * 20)
if failed:
	print("FAILED")
	exit(-2)
else:
	print("SUCCESS")
	exit(0)


