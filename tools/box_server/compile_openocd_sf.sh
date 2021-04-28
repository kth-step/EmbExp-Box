#!/usr/bin/env bash

set -e

# get base directory path
THIS_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")
BASE_DIR=$(readlink -f "${THIS_DIR}/../..")

# go to base dir
cd ${BASE_DIR}

# get and compile openocd
cd tools
rm -rf openocd_sf

git clone https://git.code.sf.net/p/openocd/code openocd_sf
cd openocd_sf

git clean -fdx .
git checkout v0.11.0
git clean -fdx .

./bootstrap
./configure --enable-jlink --enable-ftdi --enable-stlink --enable-cmsis-dap --enable-openjtag
make -j4

echo "============================"
echo "compilation of openocd done!"
echo "============================"

