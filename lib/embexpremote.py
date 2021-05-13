
import sys
import os
import threading
import time
import logging
import socket
import traceback

import boxclient
import boxportdistrib
import sshmaster
import sshslave
import embexptools


class EmbexpRemote:

	def __init__(self, instance_idx, nodes, board_type, board_option = None, node_name = None, box_name = None, board_name = None, do_query = False):
		self.instance_idx = instance_idx
		self.board_type   = board_type
		self.board_option = board_option
		self.node_name    = node_name
		self.box_name     = box_name
		self.board_name   = board_name

		box_server_port_map = {boxportdistrib.get_port_box_server_client(self.instance_idx): boxportdistrib.get_port_box_server()}

		print("trying to find a server where requested board_type is available")
		found = False
		for node in nodes:
			(node_name, ssh_host, ssh_port, node_networkmaster) = node
			if (self.node_name != None) and (self.node_name != node_name):
				continue

			print(f"trying {ssh_host} and {ssh_port}")
			try:
				master_tmp = sshmaster.SshMaster(self.instance_idx, ssh_host, ssh_port, \
							box_server_port_map, lambda: (_ for _ in ()).throw(Exception("error during server probing phase")))
				try:
					master_tmp.start()
					box_server_port_client = boxportdistrib.get_port_box_server_client(self.instance_idx)
					boxc_tmp = boxclient.BoxClient("localhost", box_server_port_client, self.board_type)
					server_query = boxc_tmp.query_server()

					if do_query:
						print(f"claimed boards at the node/server {node_name}")
						print("="*40)
						for b in server_query["claimed"]:
							print(b)
						print()
						print(f"available boards at the node/server {node_name}")
						print("="*40)
						for b in server_query["unclaimed"]:
							print(b)
						print()

					if not any(x["type"] == self.board_type for x in server_query["unclaimed"]):
						continue
				finally:
					master_tmp.stop()
			except:
				track = traceback.format_exc()
				print(track)
				print(20 * "=")
				continue
			self.ssh_host = ssh_host
			self.ssh_port = ssh_port
			print(f"choosing: {self.ssh_host} and {self.ssh_port}")
			found = True

		if not found:
			raise Exception("couldn't find a free board")

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
		if self.board_type == "genesys2":
			self.boxc.send_command("powerup_fpga_qspi")
			time.sleep(2)

		embexptools.launch_embexp_comm(self.master, self.boxc.get_board_idx(), self.boxc.get_board_id(), lambda: self.on_error("comm"))
		local_commport = boxportdistrib.get_ports_box_server_board_client(self.master.instance_idx)[0]
		boot_timeout = 20
		print(f"timeout for bootup is {boot_timeout}s")
		# TODO: the following timeout is a fix for probably wrong ssh usage, should we use -f ? how to handle if the remote port is not available?
		time.sleep(2)

		if self.board_type == "lpc11c24":
			print(f"no need to wait for {self.board_type} to boot up")

		elif self.board_type == "hikey620":
			self.boxc.send_command("powerup")
			print(f"wait for 2 seconds {self.board_type} to boot up")
			time.sleep(2)

		elif self.board_type == "genesys2":
			print(f"wait for 10 seconds for {self.board_type} to boot up")
			for i in range(10):
				print(".", end="", flush=True)
				time.sleep(1)
			print()

		elif self.board_type == "arty_a7_100t":
			assert self.board_option == "fe310"
			# TODO: generalize to use board_options (introduce a board_options string as parameter for script and variables before)
			print(f"programming FPGA with bitstream (freedom-e300) - {self.board_type}")
			embexptools.execute_embexp_programfpga(self.master, self.boxc.get_board_id(), "arty_a7_100t_riscv_freedom_e300/E300ArtyDevKitFPGAChip")

		elif self.board_type == "rpi2" or self.board_type == "rpi3" or self.board_type == "rpi4":
			print(f"waiting for {self.board_type} to boot up")
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
				bootmsg = False
				while True:
					line = ""
					while not line.endswith('\n'):
						new_b = sc.recv(1)
						try:
							new_s = new_b.decode('ascii')
						except:
							logging.debug(f"cannot decode byte: {new_b}. line so far: '{line}'")
							raise
						line = line + new_s
					logging.debug(line)
					#print(line)
					print(".", end='')
					sys.stdout.flush()
					if f"Booting board: {self.board_type}" in line:
						bootmsg = True
						#found = found + 1
					if "Init complete" in line:
						found = found + 1
						if found == 4:
							break
				print()
				#if not bootmsg:
				#	raise Exception("boot message was never seen")
			except:
				if sc != None:
					sc.close()
				raise

		else:
			raise Exception(f"don't know board type {self.board_type}")

		embexptools.launch_embexp_openocd(self.master, self.boxc.get_board_idx(), self.boxc.get_board_id(), lambda: self.on_error("openocd"))
		

	def board_reset(self):
		self.boxc.board_stop()
		self.boxc.board_start()

	def board_stop(self):
		self.boxc.board_stop()

	def on_error(self, component_name):
		logging.critical(f"{component_name} failed, stopping now")
		threading.Thread(target=self.stop_and_die, daemon=True).start()



