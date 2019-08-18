#!/usr/bin/env bash

# get base directory path
THIS_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")
BASE_DIR=$(readlink -f "${THIS_DIR}/../..")


# setup firewall (iptables)
${BASE_DIR}/tools/startup/firewall.sh

# start the box_server and fork it off
/usr/bin/python3 -u ${BASE_DIR}/tools/box_server/server.py >${BASE_DIR}/logs/box_server.log 2>&1 &


