#!/bin/bash

set -e #exit on failure

cd ..

#regenerateOutputs=yes

echo yearly
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py 40 4 >unit-tests/40-4-yearly
./simulate.py 40 4 |diff -u unit-tests/40-4-yearly -

echo 75 percent equity
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --equity-percent=75 40 4 >unit-tests/40-4-75
./simulate.py --equity-percent=75 40 4 |diff -u unit-tests/40-4-75 -

echo tent
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --equity-percent=75 --tent=30,20 40 4 >unit-tests/40-4-75-tent
./simulate.py --equity-percent=75 --tent=30,20 40 4 |diff -u unit-tests/40-4-75-tent -

echo debug
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --equity-percent=75 --debug 30 4 >unit-tests/1960-debug
./simulate.py --equity-percent=75 --debug 30 4 |diff -u unit-tests/1960-debug -

echo monthly
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --monthly 40 4 >unit-tests/40-4-monthly
./simulate.py --monthly 40 4 |diff -u unit-tests/40-4-monthly -

echo SUCCESS

