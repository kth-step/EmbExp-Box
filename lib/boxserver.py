
import socket
import threading
import _thread
import time
import os
import logging

from datetime import datetime

import messaging
import boxgpio

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
		self.claimed_last_by_user = {}
		# the gpio objects per box
		self.box_controllers = {}
		for box_id in self.config.boxes.keys():
			self.box_controllers[box_id] = boxgpio.BoxGpio(box_id, self.config.boxes[box_id])
		# the last box power off timer
		self.poweroff_timer_boxes = set()
		self.poweroff_timer = None


	def _log_info_with_time(string):
		now = datetime.now()
		datetimestr = now.strftime("%Y-%m-%d %H:%M:%S")
		logging.info(f"{datetimestr} - {string}")


	def start(self, port):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind(('0.0.0.0', port))
			s.listen(5)
			logging.info(f'Listing on port {port}...')

			self.request_handlers = { "get_board": self.socket_handle_get_board, \
						  "query_boxes": self.socket_handle_query_boxes }

			while True:
				# spawn a handler thread for each new connection
				sc, addr = s.accept()
				_thread.start_new_thread(self.socket_handle, (sc, addr))


	def socket_handle(self, sc, addr):
		try:
			with sc:
				logging.info(f"Connection established to {addr[0]}:{addr[1]}")
				#while True:
				#	messaging.send_message(sc, messaging.recv_message(sc))

				# 0a. send available request types
				request_types = list(self.request_handlers.keys())
				messaging.send_message(sc, request_types)

				# 0b. receive request type
				request = messaging.recv_message(sc)
				if not isinstance(request, list) and len(request) != 2:
					raise Exception("input error, request has to contain the request type and a user_id")
				request_type = request[0]
				user_id = request[1]
				if not request_type in request_types:
					raise Exception("input error, request type not available")

				self.request_handlers[request_type](sc, user_id)

		finally:
			logging.info(f"Connection lost with {addr[0]}:{addr[1]}")


	def socket_handle_query_boxes(self, sc, user_id):
		board_ids = set(self.config.get_boards_ids())
		with self.lock:
			claimed_boards = self.claimed_boards
			claimed_last_by_user = self.claimed_last_by_user
		board_ids_unclaimed = board_ids - claimed_boards
		boards_unclaimed = list(map(lambda x: {"id": x, "type": self.config.get_board_type(x)}, board_ids_unclaimed))
		board_ids_to_users = []
		for board_id in claimed_boards:
			board_ids_to_users.append([board_id, claimed_last_by_user[board_id]])
		messaging.send_message(sc, {"unclaimed": boards_unclaimed, "claimed": board_ids_to_users})


	def socket_handle_get_board(self, sc, user_id):
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
				board_id = self.claim_board(user_id, board_ids, user_idx)
			except BoardNotAvailableException:
				logging.warning(f"No {board_type} available")
				messaging.send_message(sc, [-1,board_id,"no board available"])
				return
			#initialize board
			try:
				self.init_board(board_id)
			except:
				logging.error(f"Error while initializing {board_id}")
				messaging.send_message(sc, [-2,board_id,"could not initialize board"])
				raise
			# claimed and initialize, inform the client
			messaging.send_message(sc, [self.config.get_board(board_id)['index'],board_id,"ok"])

			logging.info(f"Creating command handlers for board {board_id}")
			commands = {}
			if 'pin_reset' in self.config.get_board(board_id).keys():
				commands["stop"]  = lambda board_id=board_id: self.set_board_reset(board_id, True)
				commands["start"] = lambda board_id=board_id: self.set_board_reset(board_id, False)

			if "client_cmds" in self.config.get_board(board_id).keys():
				client_cmds = self.config.get_board(board_id)["client_cmds"]
				for client_cmd in client_cmds.keys():
					commands[client_cmd] = lambda board_id=board_id, client_cmd=client_cmd: self.exec_client_cmd(board_id, client_cmd)

			while True:
				# 4. send available commands
				messaging.send_message(sc, list(commands.keys()))

				# 5. receive selected command and act
				command = messaging.recv_message(sc)
				if not command in commands.keys():
					raise Exception("input error, requested command is not available")
				else:
					commands[command]()
		except messaging.SocketDiedException:
			pass
		except ConnectionResetError:
			pass
		finally:
			# always yield the board here
			self.yield_board(board_id)


	# this function has to be called from within the "box management lock"
	def set_box_power(self, box_id, withTimer = True):
		# do we need to turn on or off?
		on = box_id in set(map(lambda x: x[0], self.claimed_boards))
		# collect all unclaimed boards from this box
		unclaimedBoards = set(filter(lambda b: b[0] == box_id, self.config.get_boards_ids())) - self.claimed_boards
		# timing: delay for box powerup and poweroff (in seconds)
		powerup_waittime = 0
		if "time_powerup_wait" in self.config.get_box(box_id).keys():
			powerup_waittime = self.config.get_box(box_id)["time_powerup_wait"]
		poweroff_delay = -1
		if "time_poweroff_delay" in self.config.get_box(box_id).keys():
			poweroff_delay = self.config.get_box(box_id)["time_poweroff_delay"]

		if withTimer:
			if on:
				logging.info(f"powering on {box_id}")
				self.box_controllers[box_id].set_power(True)
				time.sleep(powerup_waittime)
				if box_id in self.poweroff_timer_boxes:
					logging.debug(f"removing {box_id} from poweroff list")
					self.poweroff_timer_boxes.remove(box_id)
				# turn off all unclaimed boards
				for board_id in unclaimedBoards:
					self.set_board_reset(board_id, True)
			else:
				if poweroff_delay >= 0:
					logging.info(f"setting timer to power off {box_id} in {poweroff_delay} seconds")
					if self.poweroff_timer != None:
						self.poweroff_timer.cancel()
					self.poweroff_timer_boxes.add(box_id)
					self.poweroff_timer = threading.Timer(poweroff_delay, self.set_box_power_off_timer)
					self.poweroff_timer.start()
		elif not on:
			logging.info(f"powering off {box_id} for real now, time expired")
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
		(box_id,board_name) = board_id
		if reset:
			logging.info(f"resetting {board_id}")
		else:
			logging.info(f"running {board_id}")
		self.box_controllers[box_id].set_board_reset(board_name, reset)

	def exec_client_cmd(self, board_id, cmd_name):
		(box_id,board_name) = board_id
		logging.info(f"executing board_cmd {cmd_name} on {board_id}")
		self.box_controllers[box_id].exec_board_cmd(board_name, cmd_name)

	def init_board(self, board_id):
		# initialize to reset
		self.set_board_reset(board_id, True)
		# no more initialization for now


	def claim_board(self, user_id, board_ids, idx=-1):
		BoxServer._log_info_with_time(f"user {user_id} tries to claim one board of {board_ids} ({idx})")
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
			# register the user_id
			self.claimed_last_by_user[board_id] = user_id
			(box_id,_) = board_id
			# ... and add it to the claimed set
			self.claimed_boards.add(board_id)
			try:
				# have to turn on the box (if needed) within the lock
				self.set_box_power(box_id)
			except:
				self.claimed_boards.remove(board_id)
				raise

		BoxServer._log_info_with_time(f"user {user_id} claimed {board_id}")
		return board_id


	def yield_board(self, board_id):
		# yield board and clean up (e.g. power off box)
		with self.lock:
			# just return if it is not really claimed yet
			if not (board_id in self.claimed_boards):
				logging.error(f"yielding but not claimed: {board_id}")
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

		BoxServer._log_info_with_time(f"yielded {board_id}")


