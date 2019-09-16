
import subprocess
import threading
import os.path
import logging


class SshSlaveNotEndedException(Exception):
	def __init__(self, slavename):
		super().__init__(slavename)

class SshSlave:
	global_sshslave_id = 0

	def __init__(self, name, master, ssh_cmds, term_handler):
		self.sshslave_id = SshSlave.global_sshslave_id
		SshSlave.global_sshslave_id = SshSlave.global_sshslave_id + 1

		self.name = name
		self.master = master
		self.ssh_cmds = ssh_cmds
		self.term_handler = term_handler

		self.term_thread = threading.Thread(target=self.run_term_check)
		self.proc = None

		# control socket
		if not os.path.exists(master.controlsocket):
			raise Exception(f"the control socket {master.controlsocket} does not exist!")
		slavessh_cmd_list = ["ssh", "-oControlPath=" + master.controlsocket]

		# construct ssh command
		self.cmd_list = slavessh_cmd_list + ["-p", str(master.ssh_port), master.ssh_host] + self.ssh_cmds

		# we use logfiles for the command outputs
		logfiledir = os.path.split(os.path.realpath(__file__))[0]+"/../logs"
		self.logfilepath = logfiledir + (f"/{self.get_name()}.log")
		if not os.path.exists(logfiledir):
			os.mkdir(logfiledir)

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()

	def get_name(self):
		return f"{self.master.get_name()}-{self.name}-{self.sshslave_id}"

	def start(self):
		assert self.master.proc != None
		assert self.proc == None
		self.master.add_slave(self)
		
		logging.debug("-- calling: " + " ".join(self.cmd_list))
		self.logfile = open(self.logfilepath, 'w')
		self.proc = subprocess.Popen(self.cmd_list, stdin=subprocess.PIPE, stdout=self.logfile, stderr=subprocess.STDOUT)
		self.term_thread.start()
	
	def stop(self, timeout=None, kill_after_timeout=False, deregister_handler=True):
		if deregister_handler:
			self.term_handler = lambda: None
		self.proc.terminate()
		self.term_thread.join(timeout)
		if self.term_thread.is_alive() and kill_after_timeout:
			self.proc.kill()
			self.term_thread.join(timeout)
		if self.term_thread.is_alive():
			raise SshSlaveNotEndedException(self.get_name())

	def run_term_check(self):
		# wait until process ends
		self.proc.wait()
		logging.debug(f"slave {self.get_name()} ended")
		self.logfile.close()
		# run the handler
		self.term_handler()


class SshSlave_Portredir(SshSlave):
	def __init__(self, master, portmap, term_handler):
		ssh_redir_params = [["-L", "127.0.0.1:%d:localhost:%d" % (k, portmap[k])] for k in portmap.keys()]
		ssh_cmd_list = [item for sublist in ssh_redir_params for item in sublist]

		SshSlave.__init__(self, "portredir", master, ssh_cmd_list, term_handler)


