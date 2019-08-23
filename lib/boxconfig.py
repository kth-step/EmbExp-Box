
import os
import json
import logging

def get_box_basedir():
	return os.path.join(os.path.dirname(__file__), "..")

class BoxConfig:
	def __init__(self):
		# read configs from json file
		with open(self.get_boxpath("config/boxes.json"), "r") as read_file:
			boxes_raw = json.load(read_file)
		# filter boxes and boards
		self.boxes = {}
		for box_k in boxes_raw.keys():
			box = boxes_raw[box_k]
			if box["active"]:
				box["boards"] = dict(filter(lambda b: b[1]["active"], box["boards"].items()))
				self.boxes[box_k] = box
		# log statistics for configurations
		#print(json.dumps(self.boxes))
		n_boxes = len(self.boxes)
		n_boards = sum(map(lambda b: len(b[1]["boards"]), self.boxes.items()))
		logging.info(f"number of boxes = {n_boxes}, number of boards = {n_boards}")
		# augment config with unique integer boardindexes
		i = 0
		for box_k in self.boxes.keys():
			for board_k in self.boxes[box_k]['boards'].keys():
				self.boxes[box_k]['boards'][board_k]['index'] = i
				i = i + 1

	def get_boxpath(self, subpath):
		return os.path.abspath(os.path.join(get_box_basedir(), subpath))

	def get_logdir(self):
		logdir = self.get_boxpath("logs")
		if not os.path.exists(logdir):
		    os.makedirs(logdir)
		return logdir

	def get_board_types(self):
		return list(set([board['Type'] for box in self.boxes.values() for board in box['boards'].values()]))

	def get_boards_ids(self):
		board_ids = []
		for box_k in self.boxes.keys():
			board_dict = self.boxes[box_k]['boards']
			box_boards = list(map(lambda board_k: (box_k, board_k), board_dict))
			board_ids.extend(box_boards)
		return set(board_ids)

	def get_boards(self, board_type):
		box_boards = []
		for box_k in self.boxes.keys():
			board_dict = self.boxes[box_k]['boards']
			filter_boards = filter(lambda boardname: board_dict[boardname]['Type'] == board_type, board_dict)
			box_boards.extend(list(map(lambda board: (box_k, board), filter_boards)))

		return box_boards

	def get_box(self, box_name):
		return self.boxes[box_name]

	def get_board(self, board_id):
		(box_name,board_name) = board_id
		return self.boxes[box_name]['boards'][board_name]


