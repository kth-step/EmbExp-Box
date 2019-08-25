#!/usr/bin/env bash

# get base directory path
THIS_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")
BASE_DIR=$(readlink -f "${THIS_DIR}/../..")

# log directory
LOG_DIR=${BASE_DIR}/logs

# setup firewall (iptables)
${BASE_DIR}/tools/startup/firewall.sh

# start the box_server and fork it off
mkdir -p ${LOG_DIR}
/usr/bin/python3 -u ${BASE_DIR}/tools/box_server/server.py >${LOG_DIR}/box_server.log 2>&1 &


