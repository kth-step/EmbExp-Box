#!/usr/bin/env python3


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import subprocess
from subprocess import call
from subprocess import Popen

import boxconfig
import toolwrapper

config = boxconfig.BoxConfig()

if len(sys.argv) <= 2:
	print("Usage: comm.py {box_name} {board_name} [interactive]")
	print("\tinteractive = 0 for tcp listener, otherwise interactive (default:1)")
	exit(-1)

board_id  = (sys.argv[1], sys.argv[2])
interactive = True
interactive_mode = ""
if len(sys.argv) > 3:
	if sys.argv[3] == "0":
		interactive = False
	else:
		interactive_mode = sys.argv[3]

try:
	board_params = config.get_board(board_id)
except:
	print("error: select a valid board")
	exit(-2)

serdev = board_params["serial_device"]
serbaud = 115200
print(f"serdev={serdev}")
print(f"serbaud={serbaud}")


board_idx = config.get_board(board_id)['index']
if board_idx > 99:
	assert False




print("=" * 20)

if interactive:
	# minicom and cat require stdin redirection

	# alternative 1: minicom
	#call(" ".join(["minicom", "-D /dev/" + ser_dev, "-b 115200"]), shell=True)

	if interactive_mode == "output":
		cmd = config.get_boxpath("tools/serial/serial_console.py")
		cmdLine = [cmd, serdev, str(serbaud)]

		toolwrapper.SimpleWrapper(cmdLine, timeout=5)
	else:
		# alternative 2: screen
		call(" ".join(["screen", serdev, str(serbaud)]), shell=True)
	exit(0)



port = 20000 + board_idx * 100 + 88

cmd = config.get_boxpath("tools/serial/tcp_serial_redirect.py")
cmdLine = [cmd, "-P", str(port), serdev, str(serbaud)]

toolwrapper.SimpleWrapper(cmdLine, timeout=5)


