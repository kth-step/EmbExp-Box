#!/usr/bin/env python3

import sys
import serial


if len(sys.argv) <= 2:
	print("Usage: serial.py {serial device} {baudrate}")
	exit(-1)

serdev = sys.argv[1]
serbaud = int(sys.argv[2])

print(f"serdev={serdev}")
print(f"serbaud={serbaud}")
print("=" * 20)

sys.stdout.flush()
with serial.Serial(serdev, serbaud) as ser:
	while True:
		data = ser.readline().decode('ascii')
		if data:
			print(data, end = '')
			sys.stdout.flush()



