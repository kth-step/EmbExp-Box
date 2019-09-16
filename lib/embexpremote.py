
import sys
import os
import threading
import time
import logging

import boxclient
import boxportdistrib
import sshmaster
import sshslave
import embexptools


class EmbexpRemote:

	def __init__(self, instance_idx, ssh_host, ssh_port, board_type, box_name = None, board_name = None):
		self.instance_idx = instance_idx
		self.ssh_host = ssh_host
		self.ssh_port = ssh_port
		self.board_type = board_type
		self.box_name = box_name
		self.board_name = board_name

		box_server_port_map = {boxportdistrib.get_port_box_server_client(self.instance_idx): boxportdistrib.get_port_box_server()}
		self.master = sshmaster.SshMaster(self.instance_idx, self.ssh_host, self.ssh_port, \
					box_server_port_map, lambda: self.on_error("master"))


	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()
		pass

	def start(self):
		# master fails if it is started twice, so remote can also not be started twice
		self.master.start()
		try:
			print("requesting board from server now")
			box_server_port_client = boxportdistrib.get_port_box_server_client(self.instance_idx)
			self.boxc = boxclient.BoxClient("localhost", box_server_port_client \
					, self.board_type, box_name=self.box_name, board_name=self.board_name)
			self.boxc.start()
			print(f"Board ID = {' '.join(self.boxc.board_id)}")
		except:
			self.master.stop()
			raise

	def stop(self):
		self.master.stop_slaves()
		self.boxc.stop()
		self.master.stop()

	def stop_and_die(self):
		self.stop()
		print("\a")
		os._exit(-1)

	def startup(self):
		embexptools.launch_embexp_comm(self.master, self.boxc.get_board_idx(), self.boxc.get_board_id(), lambda: self.on_error("comm"))

		self.boxc.board_start()
		print("connected")
		print()

		boot_time = 15
		print(f"waiting for bootup ({boot_time}s)")
		sys.stdout.flush()
		for i in range(boot_time):
			print(".", end='')
			sys.stdout.flush()
			time.sleep(1)
		print()

		embexptools.launch_embexp_openocd(self.master, self.boxc.get_board_idx(), self.boxc.get_board_id(), lambda: self.on_error("openocd"))
		

	def board_reset(self):
		self.boxc.board_stop()
		self.boxc.board_start()

	def board_stop(self):
		self.boxc.board_stop()

	def on_error(self, component_name):
		logging.critical(f"{component_name} failed, stopping now")
		threading.Thread(target=self.stop_and_die, daemon=True).start()



