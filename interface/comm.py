#!/usr/bin/env python3


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import serial
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

if "JTAG_UART_Serial" in board_params:
	serialnum = board_params["JTAG_UART_Serial"]
elif "UART_Serial" in board_params:
	serialnum = board_params["UART_Serial"]
else:
	assert False

print(f"serialnum={serialnum}")


board_idx = config.get_board(board_id)['index']
if board_idx > 99:
	assert False


# ==========================================================================
# ==========================================================================
# find all files with a certain name under a certain base path
def find_all(name, path):
	result = []
	for root, dirs, files in os.walk(path):
		if name in files:
			result.append(os.path.join(root, name))
	return result

# find all directories with a certain prefix under a certain base path
def find_all_withprefix(prefix, path):
	result = []
	for root, dirs, files in os.walk(path):
		for dir in dirs:
			#rest os.path.split(file)[1]
			#print(file)
			if dir.startswith(prefix):
				result.append(dir)
	return result

# check a file's contents to match a certain string
def match_serialnum(serialfile, serialnum):
	with open(serialfile, 'rb') as f:
		result = f.read().decode('ascii')
		#print(result)
		return result.strip() == serialnum

# find the right serial number file (supposedly by filename)
def find_serialdev_path(serialnum):
	all_sers = find_all("serial", "/sys/devices")
	matched_sers = list(filter(lambda p: match_serialnum(p, serialnum), all_sers))
	#print(f"all_sers={all_sers}")
	print(f"matched_sers={matched_sers}")

	if len(matched_sers) != 1:
		print("failed to find exactly one matching comm serial number.")
		exit(-3)
	return matched_sers[0]


# find the corresponding serial device
def find_serialdev(serfile):
	ser_devices = find_all_withprefix("ttyUSB", os.path.split(serfile)[0])
	ser_devices = list(set(ser_devices))
	print(f"ser_devices={ser_devices}")

	if len(ser_devices) != 1:
		print("failed to find exactly one matching comm device.")
		exit(-4)
	return ser_devices[0]

# ==========================================================================
# ==========================================================================

serfile = find_serialdev_path(serialnum)
ser_dev = find_serialdev(serfile)

serBaud = 115200

serPort = "/dev/" + ser_dev
serBaudS = str(serBaud)


print(ser_dev)
print("--------------------------")

if interactive:
	# minicom and cat require stdin redirection

	# alternative 1: minicom
	#call(" ".join(["minicom", "-D /dev/" + ser_dev, "-b 115200"]), shell=True)

	if interactive_mode == "output":
		sys.stdout.flush()
		with serial.Serial(serPort, serBaud) as ser:
			while True:
				data = ser.readline().decode('ascii')
				if data:
					print(data, end = '')
					sys.stdout.flush()
	else:
		# alternative 2: screen
		call(" ".join(["screen", serPort, serBaudS]), shell=True)
	exit(0)



port = 20000 + board_idx * 100 + 88

cmd = config.get_boxpath("tools/serial_redirect/tcp_serial_redirect.py")
cmdLine = [cmd, "-P", str(port), serPort, serBaudS]

toolwrapper.SimpleWrapper(cmdLine, timeout=5)


