
import os
import json
import logging

import boxconfig

class NetworkConfig:
	def __init__(self, only_active=False):
		# read configs from json file
		with open(self._get_boxpath("config/networks.json"), "r") as read_file:
			networks_raw = json.load(read_file)

		# default user
		self.default_username = networks_raw["default_username"]
		# filter networks
		self.networks = {}
		for network_k in networks_raw["networks"].keys():
			network = networks_raw["networks"][network_k]
			if network["active"]:
				network["nodes"] = dict(filter(lambda n: n[1]["active"], network["nodes"].items()))
				self.networks[network_k] = network

		# log statistics for configurations
		#print(json.dumps(self.boxes))
		n_networks = len(self.networks)
		n_nodes = sum(map(lambda n: len(n[1]["nodes"]), self.networks.items()))
		logging.info(f"number of networks = {n_networks}, number of nodes = {n_nodes}")

	def _get_boxpath(self, subpath):
		return os.path.abspath(os.path.join(boxconfig.get_box_basedir(), subpath))

	def get_node_tuples(self):
		nodes = []
		for network_k in self.networks.keys():
			network = self.networks[network_k]
			for node_k in network["nodes"].keys():
				node = network["nodes"][node_k]
				node_name = node_k
				node_port = node["port"]
				node_username = node["username"] if "username" in node.keys() else self.default_username
				node_networkmaster = network["master"]
				nodes.append((node_name, node_port, node_username, node_networkmaster))
		return nodes


