
import sys
import os
import threading
import time
import logging
import socket

import boxclient
import boxportdistrib
import sshmaster
import sshslave
import embexptools


class EmbexpRemote:

	def __init__(self, instance_idx, ssh_host, ssh_port, board_type, box_name = None, board_name = None, do_query = False):
		self.instance_idx = instance_idx
		self.ssh_host = ssh_host
		self.ssh_port = ssh_port
		self.board_type = board_type
		self.box_name = box_name
		self.board_name = board_name
		self.do_query = do_query

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
			box_server_port_client = boxportdistrib.get_port_box_server_client(self.instance_idx)

			if self.do_query:
				boxc_tmp = boxclient.BoxClient("localhost", box_server_port_client, self.board_type)
				server_query = boxc_tmp.query_server()
				print("claimed boxes at the server")
				print("="*40)
				for b in server_query["claimed"]:
					print(b)
				print()
				print("available boxes at the server")
				print("="*40)
				for b in server_query["unclaimed"]:
					print(b)
				print()

			print("requesting board from server now")
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
		local_commport = boxportdistrib.get_ports_box_server_board_client(self.master.instance_idx)[0]
		boot_timeout = 20
		print(f"timeout for bootup is {boot_timeout}s")
		# TODO: the following timeout is a fix for probably wrong ssh usage, should we use -f ? how to handle if the remote port is not available?
		time.sleep(2)

		rpi3waiting = self.board_type == "rpi3"
		if rpi3waiting:
			print("waiting for rpi3 to boot up")
			sc = None
			try:
				connected = False
				for i in range(5):
					try:
						logging.info(f"round #{i}")
						sc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
						#sc.settimeout(1)
						sc.connect(("localhost", local_commport))
						connected = True
						break
					except ConnectionRefusedError:
						logging.info(f"could not connect {i+1} times")
						time.sleep(2)
				if not connected:
					logging.critical(f"could not connect after {i+1} tries")
					raise Exception("Connection to comm could not be established")

				sc.settimeout(boot_timeout)

				# start board (starts boot process)
				self.boxc.board_start()
				print("connected and booting")
				print()
				sys.stdout.flush()

				found = 0
				while True:
					line = ""
					while not line.endswith('\n'):
						line = line + sc.recv(1).decode('ascii')
					#print(line)
					print(".", end='')
					sys.stdout.flush()
					if "Waiting for JTAG" in line:
						found = found + 1
					if "Init complete #3." in line:
						found = found + 1
						if found == 5:
							break
				print()
			except:
				if sc != None:
					sc.close()
				raise

		embexptools.launch_embexp_openocd(self.master, self.boxc.get_board_idx(), self.boxc.get_board_id(), lambda: self.on_error("openocd"))
		

	def board_reset(self):
		self.boxc.board_stop()
		self.boxc.board_start()

	def board_stop(self):
		self.boxc.board_stop()

	def on_error(self, component_name):
		logging.critical(f"{component_name} failed, stopping now")
		threading.Thread(target=self.stop_and_die, daemon=True).start()



