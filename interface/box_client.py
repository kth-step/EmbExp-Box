#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import socket
import getpass

import messaging
import boxportdistrib
import boxclient

def print_list(l):
	for i in l:
		print(i)


user_id_localpart = getpass.getuser()
user_id_remotepart = "local_boxclient"
user_id = f"{user_id_localpart}__{user_id_remotepart}"

boxc = boxclient.BoxClient("localhost", boxportdistrib.get_port_box_server(), None, user_id = user_id)
print("boxes of the server")
print("="*40)
server_query = boxc.query_server()
print("claimed:")
print_list(server_query['claimed'])
print()
print("unclaimed:")
print_list(server_query['unclaimed'])
print()
print()
print()

board_type = input("board_type: ")
board_ids = list(map(lambda x: x["id"], filter(lambda x: x["type"] == board_type, server_query["unclaimed"])))
if len(board_ids) == 0:
	raise Exception("no board to choose from")

print(board_ids)
board_idx = input("board index (server chooses if empty): ")
# select board_id based on idx or (None,None) otherwise
if board_idx == "":
	box_name   = None
	board_name = None
else:
	board_id_lst = board_ids[int(board_idx)]
	box_name   = board_id_lst[0]
	board_name = board_id_lst[1]

with boxclient.BoxClient("localhost", boxportdistrib.get_port_box_server(), board_type, box_name, board_name, user_id = user_id) as boxc:
	print(f"connected to board: {(boxc.board_idx, boxc.board_id)}")

	while True:
		print(f"available commands: {boxc.get_commands()}")

		command = input("command: ")
		if command == "":
			break
		elif command in boxc.get_commands():
			boxc.send_command(command)
		else:
			print("unavailable command")

