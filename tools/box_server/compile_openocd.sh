#!/usr/bin/env bash

set -e

# get base directory path
THIS_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")
BASE_DIR=$(readlink -f "${THIS_DIR}/../..")

# go to base dir
cd ${BASE_DIR}

# get and compile openocd
git submodule init
git submodule update
cd tools/openocd
git clean -fd
git clean -fdX
./bootstrap
./configure --enable-jlink --enable-ftdi --enable-stlink --enable-cmsis-dap --enable-openjtag
make -j4

echo "============================"
echo "compilation of openocd done!"
echo "============================"

