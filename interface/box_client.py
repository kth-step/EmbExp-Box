#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import socket
import messaging


with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sc:
	sc.connect(('localhost',35555))

	# 1. available board types
	print(messaging.recv_message(sc))

	# 2a. select type
	board_type = input("board_type: ")
	messaging.send_message(sc, board_type)

	# 2b. available boards for the selected type
	print(messaging.recv_message(sc))

	# 2c. select board
	board_id_index = input("board (server chooses if empty): ")
	if board_id_index == "":
		board_id_index = -1
	else:
		board_id_index = int(board_id_index)
	messaging.send_message(sc, board_id_index)

	# 3. receive board id or error
	(board_idx, board_id, msg) = messaging.recv_message(sc)
	print(f"idx={board_idx}, id={board_id}, msg={msg}")

	if board_idx < 0:
		print("no board available or error while initializing board")
		exit(-1)

	print("=" * 20)

	while True:
		# 4. receive commands
		print(messaging.recv_message(sc))

		# 5. send command
		command = input("command: ")
		if command == "":
			break
		messaging.send_message(sc, command)


