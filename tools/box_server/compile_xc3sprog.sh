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
cd tools/xc3sprog
git clean -fdX

OUTDIR=$(pwd)
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX:PATH="${OUTDIR}" ..
make
make install

echo "============================="
echo "compilation of xc3sprog done!"
echo "============================="

