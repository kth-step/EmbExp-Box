
import tempfile
import time

import toolwrapper


def tryOpenOcd(verbose, boxpath, interactive, board_id, sleep):
	path = boxpath + "/interface/openocd.py"
	with tempfile.TemporaryFile() as logfile:
		with toolwrapper.ToolWrapper(path, list(board_id), logfile, 5) as wrapper:
			if interactive:
				input("done? press return... ")
			else:
				time.sleep(sleep)
			wrapper.comm(data="\n".encode('ascii'), timeout=2)
		print("=" * 20)
		# check for successful output
		logfile.seek(0)
		found = 0
		for line in logfile:
			line = line.decode('ascii')
			if verbose:
				print(line, end = '')
			if "tap/device found" in line:
				found = found + 1
			if "Listening on port" in line:
				found = found + 1
			if "no device found" in line:
				return false
	return found == 7


def tryComm(verbose, boxpath, interactive, board_id, board_type, sleep):
	path = boxpath + "/interface/comm.py"
	with tempfile.TemporaryFile() as logfile:
		with toolwrapper.ToolWrapper(path, list(board_id)+["-i", "-it", "output"], logfile, 5) as wrapper:
			if interactive:
				input("done? press return... ")
			else:
				time.sleep(sleep)
			wrapper.comm(data="\n".encode('ascii'), timeout=2)
		print("=" * 20)
		# check for successful output
		logfile.seek(0)
		if board_type == "rpi3" or board_type == "rpi4":
			found = 0
			for line in logfile:
				line = line.decode('ascii')
				if verbose:
					print(line, end = '')
				if "Init complete" in line:
					found = found + 1
			return found == 4
		elif board_type == "rpi2":
			found = 0
			for line in logfile:
				line = line.decode('ascii')
				if verbose:
					print(line, end = '')
				if "U-Boot 2016.09.01-dirty" in line:
					found = found + 1
				if "RPI 2 Model B (0xa01041)" in line:
					found = found + 1
				if "reading uboot.env" in line:
					found = found + 1
			return found == 3
		else:
			raise Exception(f"unknown board type {board_type}")


