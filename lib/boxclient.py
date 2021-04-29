
import socket
import logging
import getpass

import messaging


class BoxServerNoBoardException(Exception):
	def __init__(self, message):
		super().__init__(message)


class BoxClient:
	def __init__(self, hostname, port, board_type, box_name = None, board_name = None):
		self.hostname = hostname
		self.port = port
		self.board_type = board_type
		self.box_name = box_name
		self.board_name = board_name

		self.board_id = None
		self.board_commands = None

		self.sc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	def _request_to_server(sc, request_type):
		# is this request type available?
		request_types = messaging.recv_message(sc)
		if not request_type in request_types:
			raise BoxServerNoBoardException(f"{request_type} is no available request type; available types are {request_types}")

		# send request
		user_id = getpass.getuser()
		request = [request_type, user_id]
		messaging.send_message(sc, request)

		# receive result
		return messaging.recv_message(sc)

	def query_server(self):
		with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sc:
			sc.connect((self.hostname, self.port))

			result = BoxClient._request_to_server(sc, "query_boxes")
			return result


	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.sc.close()

	def start(self):
		self.sc.connect((self.hostname, self.port))

		try:
			# select to request a board and select board type
			board_types = BoxClient._request_to_server(self.sc, "get_board")
			# fix case insensitive board type
			board_types_match = list(filter(lambda x: x.lower() == self.board_type.lower(), board_types))
			if len(board_types_match) == 1:
				self.board_type = board_types_match[0]
			if not self.board_type in board_types:
				raise BoxServerNoBoardException(f"{self.board_type} is no available board type; available types are {board_types}")
			messaging.send_message(self.sc, self.board_type)

			# select board
			board_ids = messaging.recv_message(self.sc)
			#print(board_ids)
			logging.info("requesting board")
			if self.box_name == None or self.board_name == None:
				messaging.send_message(self.sc, -1)
			else:
				board_id_choose = [self.box_name, self.board_name]
				if not board_id_choose in board_ids:
					raise BoxServerNoBoardException(f"board id {board_id_choose} is not available; available boards are {board_ids}")
				messaging.send_message(self.sc, board_ids.index(board_id_choose))

			# recieve claimed board
			(self.board_idx, self.board_id, msg) = messaging.recv_message(self.sc)
			if self.board_idx < 0:
				raise BoxServerNoBoardException(msg)

			self.board_commands = messaging.recv_message(self.sc)
		except:
			self.sc.close()
			raise

	def stop(self):
		self.sc.close()

	def get_board_idx(self):
		return self.board_idx

	def get_board_id(self):
		return self.board_id

	def get_commands(self):
		return self.board_commands

	def send_command(self, command):
		if not command in self.board_commands:
			msg = f"{command} not in {self.board_commands}"
			print(msg)
			#raise Exception(msg)
			return
		messaging.send_message(self.sc, command)
		self.board_commands = messaging.recv_message(self.sc)

	def board_start(self):
		self.send_command("start")

	def board_stop(self):
		self.send_command("stop")
