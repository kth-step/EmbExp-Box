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

target_cfg_dict = {"rpi2"     : config.get_boxpath("config/openocd/target/rpi2.cfg"), \
                   "rpi3"     : config.get_boxpath("config/openocd/target/rpi3.cfg"), \
                   "rpi4"     : config.get_boxpath("config/openocd/target/rpi4.cfg"), \
                   "lpc11c24" : "target/lpc11xx.cfg",                                 \
                   "arty_a7_100t" : config.get_boxpath("config/openocd/target/arty-a7-100t_riscv_freedom_e31.cfg"), \
                   "genesys2"     : config.get_boxpath("config/openocd/target/ariane.cfg"), \
                   "hikey620" : "target/hi6220.cfg"}
# TODO: need parameters to allow different config file (in case of different fpga configuration)

interface_cfg_extra_dict = {"rpi2"     : [], \
                            "rpi3"     : [], \
                            "rpi4"     : [], \
                            "lpc11c24" : ["-c", "adapter speed 1000"], \
                            "arty_a7_100t" : ["-c", "adapter speed 500"], \
                            "genesys2" : [], \
                            "hikey620" : ["-c", "adapter speed 500", "-c", "transport select jtag"]}

# find jtag serial number
try:
	board_params = config.get_board(board_id)
except:
	print("error: select a valid board")
	exit(-2)

_JTAG_MINIMOD_SERNUM  = "jtag_minimodule_serialnumber"
_JTAG_JTAGKEY_SERNUM  = "jtag_jtagkey_serialnumber"
_JTAG_CMSISDAP_SERNUM = "jtag_cmsisdap_serialnumber"
_JTAG_GENESYS2_SERNUM = "jtag_genesys2_serialnumber"
_JTAG_JLINK_SERNUM    = "jtag_jlink_serialnumber"
if _JTAG_MINIMOD_SERNUM in board_params:
	jtag_ftdi_serial = board_params[_JTAG_MINIMOD_SERNUM]
	interface_cfg    = "interface/ftdi/minimodule.cfg"
	command_interface_sel = ["-f", interface_cfg]
	command_interface_sel += ["-c", "ftdi_serial %s" % jtag_ftdi_serial]
elif _JTAG_JTAGKEY_SERNUM in board_params:
	jtag_ftdi_serial = board_params[_JTAG_JTAGKEY_SERNUM]
	interface_cfg    = "interface/ftdi/jtagkey.cfg"
	command_interface_sel = ["-f", interface_cfg]
	command_interface_sel += ["-c", "ftdi_serial %s" % jtag_ftdi_serial]
elif _JTAG_CMSISDAP_SERNUM in board_params:
	jtag_cmsis_serial = board_params[_JTAG_CMSISDAP_SERNUM]
	interface_cfg    = "interface/cmsis-dap.cfg"
	command_interface_sel = ["-f", interface_cfg]
	command_interface_sel += ["-c", "cmsis_dap_serial %s" % jtag_cmsis_serial]
elif _JTAG_GENESYS2_SERNUM in board_params:
	jtag_genesys2_serial = board_params[_JTAG_GENESYS2_SERNUM]
	interface_cfg    = config.get_boxpath("config/openocd/interface/ariane_jtag.cfg")
	command_interface_sel = ["-f", interface_cfg]#, "-c", "debug_level 3"]
	command_interface_sel += ["-c", "ftdi_serial %s" % jtag_genesys2_serial]
elif _JTAG_JLINK_SERNUM in board_params:
	jtag_jlink_serial = board_params[_JTAG_JLINK_SERNUM]
	interface_cfg    = "interface/jlink.cfg"
	command_interface_sel = ["-f", interface_cfg]#, "-c", "debug_level 3"]
	command_interface_sel += ["-c", "jlink serial %s" % jtag_jlink_serial]
else:
	assert False


board_idx = config.get_board(board_id)['index']
if board_idx < 0 or 99 < board_idx:
	raise Exception("board index is not usable (out of range)")

(_, ((oocd_gdb_port_base,oocd_gdb_port_len), oocd_telnet_port, oocd_tcl_port)) = boxportdistrib.get_ports_box_server_board(board_idx)

print(command_interface_sel)
print(board_id)
print(board_idx)
print(((oocd_gdb_port_base,oocd_gdb_port_len), oocd_telnet_port, oocd_tcl_port))
print(20 * "=")

os.chdir(config.get_boxpath("tools/openocd/tcl"))

board_type = board_params["type"]
commands_ports        = ["-c", "tcl_port %d"    % (oocd_tcl_port), \
			 "-c", "gdb_port %d"    % (oocd_gdb_port_base), \
			 "-c", "telnet_port %d" % (oocd_telnet_port)]
target_cfg            = target_cfg_dict[board_type]
interface_cfg_extra   = interface_cfg_extra_dict[board_type]

cmd_list = ["../src/openocd"] + command_interface_sel + (interface_cfg_extra if False else []) + commands_ports + ["-f", target_cfg] + interface_cfg_extra

toolwrapper.SimpleWrapper(cmd_list, timeout=5)


