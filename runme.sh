#! /bin/bash
export LD_LIBRARY_PATH=~/SLAT/linux/lib
export PYTHONPATH=~/SLAT/linux/lib
pushd webslat
./manage.py runserver
popd
