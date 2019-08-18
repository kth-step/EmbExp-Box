
import threading
import time

from subprocess import Popen
import subprocess


class ToolWrapperEndedException(Exception):
	def __init__(self, message):
		super().__init__(message)

# a headless toolwrapper that can only write its outputs to a file
class ToolWrapper:
	def __init__(self, path, args, logfile, terminate_timeout):
		self.path = path
		self.args = args
		self.logfile = logfile
		self.terminate_timeout = terminate_timeout
		self.started = False
          
	def __enter__(self): 
		self.start()
		return self

	def __exit__(self, exc_type, exc_value, exc_traceback):
		try:
			self.terminate()
			try:
				self.p.communicate(timeout=self.terminate_timeout)
			except subprocess.TimeoutExpired:
				self.kill()
		except ToolWrapperEndedException:
			pass

	def start(self):
		self.p = Popen([self.path] + self.args, stdin=subprocess.PIPE, stdout=self.logfile, stderr=self.logfile)
		self.started = True
		print(f"toolwrapper for {self.path} started")

	def wait(self, timeout):
		self.p.wait(timeout=timeout)

	def comm(self, data = None, timeout = None):
		self.p.communicate(data, timeout)

	def get_state(self):
		if not self.started:
			raise Exception(f"toolwrapper for {self.path} has not been started yet")
		return self.p.poll() == None

	def check_running(self):
		if not self.get_state():
			raise ToolWrapperEndedException(f"toolwrapper for {self.path} is already terminated")

	def terminate(self):
		self.check_running()
		if self.p.poll() == None:
			self.p.terminate()
			print(f"toolwrapper for {self.path}: sent signal to terminate")
		else:
			print(f"toolwrapper for {self.path} is already shut down")

	def kill(self):
		self.check_running()
		if self.p.poll() == None:
			self.p.kill()
			print(f"toolwrapper for {self.path}: sent kill signal")
		else:
			print(f"toolwrapper for {self.path} is already shut down")


# a termination helper for the simple wrapper, kills a subprocess once input arrives on stdin (apparently simething like a flush triggers this as well)
class WaitInputTerminator(threading.Thread):
	def __init__(self, p, timeout):
		threading.Thread.__init__(self,daemon=True)
		self.daemon = True
		self.p = p
		self.timeout = timeout

	def run(self):
		try:
			input()
			self.p.terminate()
			self.p.wait(timeout=self.timeout)
		finally:
			# overkill
			try:
				self.p.kill()
			except:
				pass
		

# a simple wrapper helper that returns once the process is done and terminates the process if input is provided on stdin
def SimpleWrapper(cmd_list, timeout):
	print(" ".join(cmd_list))
	print("=" * 20)
	print("press return to terminate...")
	print("=" * 20)

	with subprocess.Popen(cmd_list, stdin=subprocess.PIPE) as p:
		try:
			WaitInputTerminator(p, timeout).start()
			p.communicate()
		finally:
			# overkill
			try:
				p.kill()
			except:
				pass



