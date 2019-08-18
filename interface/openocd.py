#!/usr/bin/env python3


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import subprocess

import boxconfig
import toolwrapper

config = boxconfig.BoxConfig()


interface_cfg_dict = {"RPi3" : "../config/openocd/interface/minimodule.cfg", \
                      "RPi2" : "../config/openocd/interface/minimodule.cfg"}

target_cfg_dict = {"RPi3" : "../config/openocd/target/rpi3.cfg", \
                   "RPi2" : "../config/openocd/target/rpi2.cfg" }


if len(sys.argv) <= 2:
	print("Usage: openocd.py {box_name} {board_name}")
	exit(-1)

board_id  = (sys.argv[1], sys.argv[2])
try:
	board_params = config.get_board(board_id)
except:
	print("error: select a valid board")
	exit(-2)

if "JTAG_UART_Serial" in board_params:
	jtag_ftdi_serial = board_params["JTAG_UART_Serial"]
elif "JTAG_Serial" in board_params:
	jtag_ftdi_serial = board_params["JTAG_Serial"]
else:
	assert False


board_idx = config.get_board(board_id)['index']
if board_idx > 99:
	assert False
base_port = 20000 + board_idx * 100

print(jtag_ftdi_serial)
print(board_id)
print(board_idx)
print(base_port)
print("--------------------")



os.chdir(config.get_boxpath("tools"))

board_type = board_params["Type"]
interface_cfg         = interface_cfg_dict[board_type]
command_interface_sel = ["-c", "ftdi_serial %s" % jtag_ftdi_serial]
commands_ports        = ["-c", "tcl_port %d"    % (base_port + 66), \
			 "-c", "gdb_port %d"    % (base_port + 33), \
			 "-c", "telnet_port %d" % (base_port + 44)]
target_cfg            = target_cfg_dict[board_type]

cmd_list = ["openocd/src/openocd", "-f", interface_cfg] + command_interface_sel + commands_ports + ["-f", target_cfg]

#oocd_stdout = subprocess.DEVNULL
#oocd_stdout = subprocess.STDOUT

toolwrapper.SimpleWrapper(cmd_list, timeout=5)


