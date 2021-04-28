
import logging
import time

from nanpy import SerialManager
from nanpy import ArduinoApi

class BoxGpio:
	_PARAM_PIN_CONTROLLER = "pin_controller"
	_PARAM_PIN_POWER = "pin_power"
	_PARAM_PIN_FAN = "pin_fan"
	_PARAM_BOARD_PIN_RESET = "pin_reset"

	def __init__(self, box_id, config_box):
		self.box_id = box_id
		self.config_box = config_box

		if not BoxGpio._PARAM_PIN_CONTROLLER in self.config_box:
			self.arduino = None
			logging.info(f"Box {self.box_id} has no pin controller")
		else:
			connection = SerialManager(device=self.config_box[BoxGpio._PARAM_PIN_CONTROLLER])
			self.arduino = ArduinoApi(connection=connection)

		self.set_power(False)
		self.set_fan(0)


	def set_power(self, on):
		if self.arduino == None:
			return
		if not BoxGpio._PARAM_PIN_POWER in self.config_box:
			return

		self._set_pin(self.config_box[BoxGpio._PARAM_PIN_POWER], not on)
		logging.info(f"Box {self.box_id} <- power={on}")


	def set_fan(self, val):
		if self.arduino == None:
			return
		if not BoxGpio._PARAM_PIN_FAN in self.config_box:
			return

		val = min(1, max(0, val))
		# TODO: this could be changed to pwm if required
		self._set_pin(self.config_box[BoxGpio._PARAM_PIN_FAN], False)
		logging.info(f"Box {self.box_id} <- fan={val}")


	def set_board_reset(self, board_name, reset):
		if self.arduino == None:
			return
		board = self.config_box['boards'][board_name]
		if not BoxGpio._PARAM_BOARD_PIN_RESET in board:
			# this is a hack
			if reset and self.board_cmd_exists(board_name, "poweroff"):
				self.exec_board_cmd(board_name, "poweroff")
				logging.info(f"Box {self.box_id} <- {board_name}.poweroff")
			return

		self._set_pin(board[BoxGpio._PARAM_BOARD_PIN_RESET], not reset)
		logging.info(f"Box {self.box_id} <- {board_name}.reset={not reset}")


	def board_cmd_exists(self, board_name, cmd_name):
		board_config = self.config_box['boards'][board_name]
		if not("client_cmds" in board_config):
			return False
		return cmd_name in board_config["client_cmds"]


	def exec_board_cmd(self, board_name, cmd_name):
		cmd_seq = self.config_box['boards'][board_name]["client_cmds"][cmd_name]
		logging.info(f"Box {self.box_id} <- {board_name}.{cmd_name} - {cmd_seq}")
		for instr in cmd_seq:
			instr_p = instr.split(" ")
			assert len(instr_p) >= 1
			op  = instr_p[0]
			par = instr_p[1:]
			if op == "sleep":
				assert len(par) == 1
				time.sleep(float(par[0]))
			elif op == "pin":
				assert len(par) == 2
				pin = int(par[0])
				assert par[1] == "true" or par[1] == "false"
				val = par[1] != "false"
				self._set_pin(pin, val)
			else:
				raise Exception(f"unknown instruction '{op}'")


	def _set_pin(self, pin, on):
		if self.arduino == None:
			raise Exception(f"no pin controller at {self.box_id}")

		if on:
			# on means floating! this is important!
			self.arduino.digitalWrite(pin, self.arduino.LOW)
			self.arduino.pinMode(pin, self.arduino.INPUT)
		else:
			self.arduino.pinMode(pin, self.arduino.OUTPUT)
			self.arduino.digitalWrite(pin, self.arduino.LOW)
		
		logging.debug(f"Box {self.box_id} <- pin{pin}={on}")



