#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import argparse
import subprocess

import boxconfig
import toolwrapper
import boxportdistrib

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("box_name", help="name of the box to connect to")
parser.add_argument("board_name", help="name of the board to connect to")
parser.add_argument("-i", "--interactive", help="interactive comm session, otherwise hosted as tcp port", action="store_true")
parser.add_argument("-it", "--interactiveType", help="if interactive, what type (\"output\" means output only)")
args = parser.parse_args()

# argument variables
board_id  = (args.box_name, args.board_name)
interactive = args.interactive
interactive_mode = args.interactiveType


# load config
config = boxconfig.BoxConfig()

# find serial device path
try:
	board_params = config.get_board(board_id)
except:
	print("error: select a valid board")
	exit(-1)

serdev = board_params["serial_device"]
# TODO: have a better solution for baudrate selection
serbaud = 9600 if board_params["Type"] == "LPC11C24" else 115200
print(f"serdev={serdev}")
print(f"serbaud={serbaud}")


board_idx = config.get_board(board_id)['index']
if board_idx < 0 or 99 < board_idx:
	raise Exception("board index is not usable (out of range)")




print("=" * 20)

if interactive:
	# minicom and cat require stdin redirection

	# alternative 1: minicom
	#subprocess.call(" ".join(["minicom", "-D /dev/" + ser_dev, "-b 115200"]), shell=True)

	if interactive_mode == "output":
		cmd = config.get_boxpath("tools/serial/serial_console.py")
		cmdLine = [cmd, serdev, str(serbaud)]

		toolwrapper.SimpleWrapper(cmdLine, timeout=5)
	else:
		# alternative 2: screen
		subprocess.call(" ".join(["screen", serdev, str(serbaud)]), shell=True)
	exit(0)



(comm_port, _) = boxportdistrib.get_ports_box_server_board(board_idx)

cmd = config.get_boxpath("tools/serial/tcp_serial_redirect.py")
cmdLine = [cmd, "-P", str(comm_port), serdev, str(serbaud)]

toolwrapper.SimpleWrapper(cmdLine, timeout=5)


