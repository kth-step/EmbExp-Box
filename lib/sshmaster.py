
import subprocess
import threading
import os
import os.path
import logging

class SshMaster:
	def __init__(self, instance_idx, ssh_host, ssh_port, port_map, term_handler):
		self.instance_idx = instance_idx
		self.ssh_port = ssh_port
		self.ssh_host = ssh_host
		self.port_map = port_map
		self.term_handler = term_handler

		self.slaves = []
		self.term_thread = threading.Thread(target=self.run_term_check)
		self.proc = None

		# ssh command and control socket handling
		self.controlsocket = os.path.split(os.path.realpath(__file__))[0]+f"/../ssh/embexp-remote-inst_{self.instance_idx}.sock"
		slavessh_cmd_list = ["-oControlPath=" + self.controlsocket]
		masterssh_cmd_list = slavessh_cmd_list + ["-oControlMaster=yes"]

		ssh_host_cmd_list = ["-p", str(ssh_port), ssh_host]
		ssh_check_cmd_list = ["-Ocheck"]

		# check if the control socket is usable (i.e. whether this master instance is already running)
		if os.path.exists(self.controlsocket):
			if subprocess.call(["ssh"] + slavessh_cmd_list + ssh_host_cmd_list + ssh_check_cmd_list) == 0:
				raise Exception(f"master {self.get_name()} is already running")
			os.remove(self.controlsocket)
			logging.warning("NOTICE: the control socket still existed, deleted it now")

		# create socket directory if it doesn't exist yet
		controlsocketdir = os.path.split(self.controlsocket)[0]
		if not os.path.exists(controlsocketdir):
			os.mkdir(controlsocketdir)

		# forwarding to box_server
		portmap = self.port_map
		ssh_redir_params = [["-L", "127.0.0.1:%d:localhost:%d" % (k, portmap[k])] for k in portmap.keys()]
		ssh_redir_cmd_list = [item for sublist in ssh_redir_params for item in sublist]

		# use keep alive messages
		ssh_keep_alive_list = ["-oServerAliveInterval=60"]

		# construct the ssh command
		self.cmd_list = ["ssh"] + ssh_keep_alive_list + masterssh_cmd_list + ssh_redir_cmd_list + ssh_host_cmd_list

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()

	def get_name(self):
		return f"inst_{self.instance_idx}"

	def add_slave(self, slave):
		self.slaves.append(slave)


	def start(self):
		assert self.proc == None

		# TODO: detect when port redirection fails, the same in slave!

		logging.debug("-- calling: " + " ".join(self.cmd_list))
		self.proc = subprocess.Popen(self.cmd_list, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		self.term_thread.start()
		# wait until connection is established (a command can be executed)
		magicstring = "I am alive!"
		self.proc.stdin.write(f"echo \"{magicstring}\"\n".encode('ascii'))
		self.proc.stdin.flush()
		try:
			while True:
				line = next(self.proc.stdout).decode('ascii')
				#print(line, end = '')
				if magicstring in line:
					break
		except StopIteration:
			raise Exception("master ssh ended while connecting")

	def stop_slaves(self, slavetimeout=None):
		slaves_to_stop = list(self.slaves)
		for slave in slaves_to_stop:
			slave.stop(timeout=slavetimeout)
			self.slaves.remove(slave)

	def stop(self, slavetimeout=None):
		# stop slaves
		self.stop_slaves(slavetimeout)
		# stop myself
		self.term_handler = lambda: None
		try:
			self.proc.stdin.write("exit\n".encode('ascii'))
			self.proc.stdin.flush()
		except BrokenPipeError:
			logging.debug(f"master {self.get_name()} already ended")
		self.term_thread.join(timeout=10) # timeout for the unforeseen
		if self.term_thread.is_alive():
			logging.debug(f"master {self.get_name()} did not terminate by itself, sending terminate signal now")
			self.proc.terminate()
			self.term_thread.join()

	def run_term_check(self):
		# wait until process ends
		self.proc.wait()
		logging.debug(f"master {self.get_name()} ended")
		# run the handler
		self.term_handler()






