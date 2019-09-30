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

target_cfg_dict = {"RPi2"     : config.get_boxpath("config/openocd/target/rpi2.cfg"), \
                   "RPi3"     : config.get_boxpath("config/openocd/target/rpi3.cfg"), \
                   "RPi4"     : config.get_boxpath("config/openocd/target/rpi4.cfg"), \
                   "LPC11C24" : "target/lpc11xx.cfg"}

target_cfg_extra_dict = {"RPi2"     : [], \
                         "RPi3"     : [], \
                         "RPi4"     : [], \
                         "LPC11C24" : ["-c", "adapter_khz 1000"]}

# find jtag serial number
try:
	board_params = config.get_board(board_id)
except:
	print("error: select a valid board")
	exit(-2)

_JTAG_MINIMOD_SERNUM = "jtag_minimodule_serialnumber"
_JTAG_CMSISDAP_SERNUM = "jtag_cmsisdap_serialnumber"
if _JTAG_MINIMOD_SERNUM in board_params:
	jtag_ftdi_serial = board_params[_JTAG_MINIMOD_SERNUM]
	interface_cfg    = config.get_boxpath("config/openocd/interface/minimodule.cfg")
	command_interface_sel = ["-c", "ftdi_serial %s" % jtag_ftdi_serial]
elif _JTAG_CMSISDAP_SERNUM in board_params:
	jtag_cmsis_serial = board_params[_JTAG_CMSISDAP_SERNUM]
	interface_cfg    = "interface/cmsis-dap.cfg"
	command_interface_sel = ["-c", "cmsis_dap_serial %s" % jtag_cmsis_serial]
else:
	assert False


board_idx = config.get_board(board_id)['index']
if board_idx < 0 or 99 < board_idx:
	raise Exception("board index is not usable (out of range)")

(_, ((oocd_gdb_port_base,oocd_gdb_port_len), oocd_telnet_port, oocd_tcl_port)) = boxportdistrib.get_ports_box_server_board(board_idx)

print(interface_cfg)
print(command_interface_sel)
print(board_id)
print(board_idx)
print(((oocd_gdb_port_base,oocd_gdb_port_len), oocd_telnet_port, oocd_tcl_port))
print(20 * "=")

os.chdir(config.get_boxpath("tools/openocd/tcl"))

board_type = board_params["Type"]
commands_ports        = ["-c", "tcl_port %d"    % (oocd_tcl_port), \
			 "-c", "gdb_port %d"    % (oocd_gdb_port_base), \
			 "-c", "telnet_port %d" % (oocd_telnet_port)]
target_cfg            = target_cfg_dict[board_type]
target_cfg_extra      = target_cfg_extra_dict[board_type]

cmd_list = ["../src/openocd", "-f", interface_cfg] + command_interface_sel + commands_ports + ["-f", target_cfg] + target_cfg_extra

toolwrapper.SimpleWrapper(cmd_list, timeout=5)


