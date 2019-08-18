
from nanpy import SerialManager
from nanpy import ArduinoApi

class BoxGpio:
	def __init__(self, box_id, box_params):
		self.box_id = box_id
		self.pin_power = box_params['pin_power']
		self.pin_fan = box_params['pin_fan']
		self.initd_pins = set()

		pin_controller = box_params['pin_controller']
		connection = SerialManager(device=pin_controller)
		self.arduino = ArduinoApi(connection=connection)

		self.set_power(False)
		self.set_fan(0)


	def set_power(self, on):
		self.set_pin(self.pin_power, not on)


	def set_fan(self, val):
		val = min(1, max(0, val))
		self.set_pin(self.pin_fan, False)
		print(f"Box {self.box_id} <- fan={val}")


	def set_pin(self, pin, on):
		if not pin in self.initd_pins:
			self.arduino.pinMode(pin, self.arduino.OUTPUT)
			self.initd_pins.add(pin)

		if on:
			# on means floating! this is important!
			self.arduino.digitalWrite(pin, self.arduino.LOW)
			self.arduino.pinMode(pin, self.arduino.INPUT)
		else:
			self.arduino.pinMode(pin, self.arduino.OUTPUT)
			self.arduino.digitalWrite(pin, self.arduino.LOW)
		
		print(f"Box {self.box_id} <- pin{pin}={on}")



