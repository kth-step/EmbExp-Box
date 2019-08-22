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
args = parser.parse_args()

# argument variables
board_id  = (args.box_name, args.board_name)


# load config
config = boxconfig.BoxConfig()

interface_cfg_dict = {"RPi3" : "../config/openocd/interface/minimodule.cfg", \
                      "RPi2" : "../config/openocd/interface/minimodule.cfg"}

target_cfg_dict = {"RPi3" : "../config/openocd/target/rpi3.cfg", \
                   "RPi2" : "../config/openocd/target/rpi2.cfg" }

# find jtag serial number
try:
	board_params = config.get_board(board_id)
except:
	print("error: select a valid board")
	exit(-2)

_JTAG_MINIMOD_SERNUM = "jtag_minimodule_serialnumber"
if _JTAG_MINIMOD_SERNUM in board_params:
	jtag_ftdi_serial = board_params[_JTAG_MINIMOD_SERNUM]
else:
	assert False


board_idx = config.get_board(board_id)['index']
if board_idx < 0 or 99 < board_idx:
	raise Exception("board index is not usable (out of range)")

(_, ((oocd_gdb_port_base,oocd_gdb_port_len), oocd_telnet_port, oocd_tcl_port)) = boxportdistrib.get_ports_box_server_board(board_idx)

print(jtag_ftdi_serial)
print(board_id)
print(board_idx)
print(((oocd_gdb_port_base,oocd_gdb_port_len), oocd_telnet_port, oocd_tcl_port))
print(20 * "=")

os.chdir(config.get_boxpath("tools"))

board_type = board_params["Type"]
interface_cfg         = interface_cfg_dict[board_type]
command_interface_sel = ["-c", "ftdi_serial %s" % jtag_ftdi_serial]
commands_ports        = ["-c", "tcl_port %d"    % (oocd_tcl_port), \
			 "-c", "gdb_port %d"    % (oocd_gdb_port_base), \
			 "-c", "telnet_port %d" % (oocd_telnet_port)]
target_cfg            = target_cfg_dict[board_type]

cmd_list = ["openocd/src/openocd", "-f", interface_cfg] + command_interface_sel + commands_ports + ["-f", target_cfg]

toolwrapper.SimpleWrapper(cmd_list, timeout=5)


