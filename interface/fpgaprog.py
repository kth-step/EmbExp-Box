#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

import argparse
import subprocess

import boxconfig

firmware_file_dir = "tools/firmware/fpga"

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("box_name", help="name of the box to connect to")
parser.add_argument("board_name", help="name of the board to connect to")
parser.add_argument("firmware", help=f"firmware file prefix to load to the fpga, relative to {firmware_file_dir} and without suffix .bit/.mcs, e.g. \"arty_a7_100t_riscv_freedom_e300/E300ArtyDevKitFPGAChip\"")
parser.add_argument("--to_flash", help="write the firmware (.mcs) to flash", action="store_true")
args = parser.parse_args()


# argument variables
board_id  = (args.box_name, args.board_name)
to_flash = args.to_flash
firmware_file = args.firmware + (".mcs" if to_flash else ".bit")


# load config
config = boxconfig.BoxConfig()

# find device parameters
try:
	board_params = config.get_board(board_id)
except:
	print("error: select a valid board")
	exit(-1)

# we only have one board type that this script can handle at the moment
assert(board_params["type"] == "arty_a7_100t")
print(f"board_type = {board_params['type']}")

# find the usb connection serial number to connect to the fpga
_JTAG_ARTY_SERNUM = "fpga_arty_jtag_serialnumber"
assert(_JTAG_ARTY_SERNUM in board_params)
fpga_jtag_serial = board_params[_JTAG_ARTY_SERNUM]

# get bitstream filename
firmware_file_path = config.get_boxpath(os.path.join(firmware_file_dir, firmware_file))
assert(os.path.isfile(firmware_file_path))

if not to_flash:
	jtag_prog_cmd = [config.get_boxpath("tools/xc3sprog/bin/xc3sprog"), "-c", "nexys4", "-s", fpga_jtag_serial, firmware_file_path]
	print(" ".join(jtag_prog_cmd))
	print(20 * "=")

	subprocess.call(jtag_prog_cmd)
else:
	# get the parameters (TODO: there are more)
	fpga_ftdi_serial = "T1RZQ4MO"
	fpga_openocd_cfg = config.get_boxpath("config/openocd/target/arty-a7-100t_riscv_freedom_e31.cfg")

	# program the FPGA (.bit file)
	cmd_1 = [config.get_boxpath("interface/fpgaprog.py"), board_id[0], board_id[1], "arty_a7_100t_riscv_freedom_e300/E300ArtyDevKitFPGAChip"]
	print(" ".join(cmd_1))
	print(20 * "=")
	# TODO: execute cmd_1 here

	print(20 * "=")
	print("==== DONE")
	print(20 * "=")


	# use the softcore JTAG connection to program the flash memory (.mcs file)
	print("cd tools/openocd/tcl")
	cmd_2 = ["../src/openocd", "-c", "adapter_khz 2000", "-f", "interface/ftdi/jtagkey.cfg", "-c", f"ftdi_serial {fpga_ftdi_serial}", "-f", fpga_openocd_cfg, "-c", "flash protect 0 0 last off", "-c", f"program {firmware_file_path} verify 0x20000000", "-c", "exit"]
	print(" ".join(cmd_2))
	print(20 * "=")
	print("note: it normally takes about 3 minutes to write and then 2 minutes to verify")
	print(20 * "=")
	# TODO: execute cmd_2 here

	print(20 * "=")
	print("==== DONE")
	print(20 * "=")
	print("TODO: test this, is not executed at the moment")

