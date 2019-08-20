#!/usr/bin/env python3


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))

import boxconfig
import boxserver

import logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

config = boxconfig.BoxConfig()

server = boxserver.BoxServer(config)

server.start(35555)

