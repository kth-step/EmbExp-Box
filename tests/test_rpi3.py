#!/usr/bin/python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import socket
import messaging
import boxconfig
import toolwrapper
import tempfile
import time


config = boxconfig.BoxConfig()

interactive = False
if len(sys.argv) > 1 and sys.argv[1] != "0":
	interactive = True


def tryOpenOcd(board_id, sleep):
	path = config.get_boxpath("interface/openocd.py")
	with tempfile.TemporaryFile() as logfile:
		with toolwrapper.ToolWrapper(path, list(board_id), logfile, 5) as wrapper:
			if interactive:
				input("done? press return... ")
			else:
				time.sleep(sleep)
			wrapper.comm()
		print("=" * 20)
		# check for successful output
		logfile.seek(0)
		found = 0
		for line in logfile:
			line = line.decode('ascii')
			#print(line, end = '')
			if "tap/device found" in line:
				found = found + 1
			if "Listening on port" in line:
				found = found + 1
			if "no device found" in line:
				return false
	return found == 7


def tryComm(board_id, sleep):
	path = config.get_boxpath("interface/comm.py")
	with tempfile.TemporaryFile() as logfile:
		with toolwrapper.ToolWrapper(path, list(board_id)+["output"], logfile, 5) as wrapper:
			if interactive:
				input("done? press return... ")
			else:
				time.sleep(sleep)
			wrapper.kill()
			wrapper.comm(timeout=2)
		print("=" * 20)
		# check for successful output
		logfile.seek(0)
		found = 0
		for line in logfile:
			line = line.decode('ascii')
			#print(line, end = '')
			if "Waiting for JTAG" in line:
				found = found + 1
			if "Init complete #3." in line:
				found = found + 1
	return found == 5

failed = False
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sc:
	sc.connect(('localhost',35555))

	# 0. select request
	request = "get_board"
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
	if tryComm(board_id, 15):
		print("SUCCESS: Comm")
	else:
		print("FAILED: Comm")
		failed = True

	print("=" * 20)
	if tryOpenOcd(board_id, 5):
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


