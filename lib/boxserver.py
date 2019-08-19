
import socket
import threading
import _thread
import time
import os

import messaging
import boxgpio
import toolwrapper

class BoardNotAvailableException(Exception):
	pass

class BoxServer:
	def __init__(self, config):
		self.config = config
		self.logdir = config.get_logdir()
		# create a global server lock
		self.lock = threading.Lock()
		# the set of claimed boards, is protected by the lock
		self.claimed_boards = set()
		# the gpio objects per box
		self.box_controllers = {}
		for box_id in self.config.boxes.keys():
			self.box_controllers[box_id] = boxgpio.BoxGpio(box_id, self.config.boxes[box_id])
		# the last box power off timer
		self.poweroff_timer_boxes = set()
		self.poweroff_timer = None


	def start(self, port):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind(('0.0.0.0', port))
			s.listen(5)
			print(f'Listing on port {port}...')

			

			while True:
				# spawn a handler thread for each new connection
				sc, addr = s.accept()
				_thread.start_new_thread(self.socket_handle, (sc, addr))


	def socket_handle(self, sc, addr):
		try:
			with sc:
				print(f"Connection established to {addr[0]}:{addr[1]}")
				#while True:
				#	messaging.send_message(sc, messaging.recv_message(sc))

				# 0a. send available request types
				messaging.send_message(sc, ["get_board"])
				
				# 0b. receive request type
				request = messaging.recv_message(sc)
				if request != "get_board":
					raise Exception("input error, request not available")

				# 1. send available board types
				board_types = self.config.get_board_types()
				messaging.send_message(sc, board_types)

				# 2a. receive required board
				board_type = messaging.recv_message(sc)
				if not board_type in board_types:
					raise Exception("input error, requested board type is not available")

				# 2b. send available board_ids
				board_ids = set(self.config.get_boards(board_type))
				with self.lock: # for safety under the lock
					board_ids = board_ids - self.claimed_boards
				board_ids = list(board_ids)
				messaging.send_message(sc, board_ids)

				# 2c. take selection as "wish index" relative to the list of boards sent before, unless negative
				user_idx = messaging.recv_message(sc)
				if not isinstance(user_idx, int):
					raise Exception("input format error, board_index")
				if (user_idx >= 0) and (user_idx >= len(board_ids)):
					raise Exception("input format error, board_index")

				# 3. claim one from the available boards and send its name
				board_id = -1
				try:
					# calim board
					try:
						board_id = self.claim_board(board_ids, user_idx)
					except BoardNotAvailableException:
						print(f"No {board_type} available")
						messaging.send_message(sc, [-1,board_id,"no board available"])
						return
					#initialize board
					try:
						self.init_board(board_id)
					except:
						print(f"Error while initializing {board_id}")
						messaging.send_message(sc, [-2,board_id,"could not initialize board"])
						raise
					# claimed and initialize, inform the client
					messaging.send_message(sc, [self.config.get_board(board_id)['index'],board_id,"ok"])

					while True:
						# 4. send available commands
						messaging.send_message(sc, ["stop", "start"])

						# 5. receive selected command and act
						command = messaging.recv_message(sc)
						if command == "stop":
							self.set_board_reset(board_id, True)
						if command == "start":
							self.set_board_reset(board_id, False)
				except messaging.SocketDiedException:
					pass
				except ConnectionResetError:
					pass
				finally:
					# always yield the board here
					self.yield_board(board_id)
		finally:
			print(f"Connection lost with {addr[0]}:{addr[1]}")


	# this function has to be called from within the "box management lock"
	def set_box_power(self, box_id, withTimer = True):
		# do we need to turn on or off?
		on = box_id in set(map(lambda x: x[0], self.claimed_boards))
		# collect all unclaimed boards from this box
		unclaimedBoards = set(filter(lambda b: b[0] == box_id, self.config.get_boards_ids())) - self.claimed_boards
		# timing: delay for box powerup and poweroff (in seconds)
		powerup_waittime = self.config.get_timing("box_powerup_wait")
		poweroff_delay = self.config.get_timing("box_poweroff_delay")

		if withTimer:
			if on:
				print(f"powering on {box_id}")
				self.box_controllers[box_id].set_power(True)
				time.sleep(powerup_waittime)
				if box_id in self.poweroff_timer_boxes:
					print(f"removing {box_id} from poweroff list")
					self.poweroff_timer_boxes.remove(box_id)
				# turn off all unclaimed boards
				for board_id in unclaimedBoards:
					self.set_board_reset(board_id, True)
			else:
				print(f"setting timer to power off {box_id} in {poweroff_delay} seconds")
				if self.poweroff_timer != None:
					self.poweroff_timer.cancel()
				self.poweroff_timer_boxes.add(box_id)
				self.poweroff_timer = threading.Timer(poweroff_delay, self.set_box_power_off_timer)
				self.poweroff_timer.start()
		elif not on:
			print(f"powering off {box_id} for real now, time expired")
			self.box_controllers[box_id].set_power(False)
		else:
			# we should never get here beause of our lock
			assert False


	def set_box_power_off_timer(self):
		# use the currently claimed boards and see whether we could turn off now after the last timer expired
		with self.lock:
			for box_id in self.poweroff_timer_boxes:
				self.set_box_power(box_id, False)
			self.poweroff_timer_boxes.clear()
			self.poweroff_timer = None


	def set_board_reset(self, board_id, reset):
		(box_id,_) = board_id
		pin_reset = self.config.get_board(board_id)['pin_reset']
		if reset:
			print(f"resetting {board_id}")
		else:
			print(f"running {board_id}")
		self.box_controllers[box_id].set_pin(pin_reset, not reset)


	def init_board(self, board_id):
		# initialize to reset
		self.set_board_reset(board_id, True)
		# timing
		oocd_runtime = self.config.get_timing("board_init_oocd_run")
		oocd_termtime = self.config.get_timing("board_init_oocd_term")
		# initialize openocd
		logfilename = "boxserver.py_oocdinit_brd_" + str(self.config.get_board(board_id)['index']) + ".log"
		logpath = os.path.join(self.logdir,logfilename)
		oocdpath = self.config.get_boxpath("interface/openocd.py")
		with open(logpath, 'w') as logfile:
			with toolwrapper.ToolWrapper(oocdpath, list(board_id), logfile, oocd_termtime) as oocdwrapper:
				print(f"oocd init {board_id} --- logging: {logpath}")
				oocdwrapper.wait(oocd_runtime)
		with open(logpath, 'r') as logfile:
			found = False
			for line in logfile:
				if "STICKY ERROR" in line:
					found = True
					break
			if not found:
				raise Exception("openocd could not initialize the jtag port according to the output")


	def claim_board(self, board_ids, idx=-1):
		# have to determine which ones are not in use, turn on the box maybe
		with self.lock:
			# first select a board
			if idx < 0:
				board_ids = set(board_ids) - self.claimed_boards
				if len(board_ids) == 0:
					raise BoardNotAvailableException()
				board_id = next(iter(board_ids))
			else:
				board_id = board_ids[idx]
			# check whether selection is already claimed
			if board_id in self.claimed_boards:
				raise BoardNotAvailableException()
			(box_id,_) = board_id
			# ... and add it to the claimed set
			self.claimed_boards.add(board_id)
			try:
				# have to turn on the box (if needed) within the lock
				self.set_box_power(box_id)
			except:
				self.claimed_boards.remove(board_id)
				raise

		print(f"claimed {board_id}")
		return board_id


	def yield_board(self, board_id):
		# yield board and clean up (e.g. power off box)
		with self.lock:
			# just return if it is not really claimed yet
			if not (board_id in self.claimed_boards):
				print(f"yielding but not claimed: {board_id}")
				return
			(box_id,_) = board_id
			# remove it from the claimed set
			self.claimed_boards.remove(board_id)
			# try to keep board in reset
			try:
				self.set_board_reset(board_id, True)
			except:
				pass
			# have to turn off the box (if not needed) within the lock
			self.set_box_power(box_id)

		print(f"yielded {board_id}")


