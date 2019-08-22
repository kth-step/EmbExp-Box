#!/usr/bin/env python3

import sys
import serial
import argparse

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("serdev", help="path to the serial device")
parser.add_argument("baudrate", help="baudrate to use", type=int)
args = parser.parse_args()

# argument variables
serdev = args.serdev
serbaud = args.baudrate

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



