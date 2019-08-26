#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))

import argparse
import logging

import boxconfig
import boxserver
import boxportdistrib

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
args = parser.parse_args()

# set log level
if args.verbose:
	logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
else:
	logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# start server
config = boxconfig.BoxConfig(only_active=True)
server = boxserver.BoxServer(config)

try:
	server.start(boxportdistrib.get_port_box_server())
except KeyboardInterrupt:
	logging.info("keyboard interrupt, stopping server")


