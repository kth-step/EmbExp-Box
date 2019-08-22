
import tempfile
import time

import toolwrapper


def tryOpenOcd(boxpath, interactive, board_id, sleep):
	path = boxpath + "/interface/openocd.py"
	with tempfile.TemporaryFile() as logfile:
		with toolwrapper.ToolWrapper(path, list(board_id), logfile, 5) as wrapper:
			if interactive:
				input("done? press return... ")
			else:
				time.sleep(sleep)
			wrapper.comm()
		print("=" * 20)
		# check for successful output
		logfile.seek(0)
		found = 0
		for line in logfile:
			line = line.decode('ascii')
			#print(line, end = '')
			if "tap/device found" in line:
				found = found + 1
			if "Listening on port" in line:
				found = found + 1
			if "no device found" in line:
				return false
	return found == 7


def tryCommRpi3(boxpath, interactive, board_id, sleep):
	path = boxpath + "/interface/comm.py"
	with tempfile.TemporaryFile() as logfile:
		with toolwrapper.ToolWrapper(path, list(board_id)+["-i", "-it", "output"], logfile, 5) as wrapper:
			if interactive:
				input("done? press return... ")
			else:
				time.sleep(sleep)
			wrapper.kill()
			wrapper.comm(timeout=2)
		print("=" * 20)
		# check for successful output
		logfile.seek(0)
		found = 0
		for line in logfile:
			line = line.decode('ascii')
			#print(line, end = '')
			if "Waiting for JTAG" in line:
				found = found + 1
			if "Init complete #3." in line:
				found = found + 1
	return found == 5
