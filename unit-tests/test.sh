#!/bin/bash

set -e #exit on failure

cd ..

echo yearly
./simulate.py 40 4 |diff -u unit-tests/40-4-yearly -

echo 75 percent equity
./simulate.py --equity-ratio=.75 40 4 |diff -u unit-tests/40-4-75 -

echo monthly
./simulate.py --monthly 40 4 |diff -u unit-tests/40-4-monthly -

echo SUCCESS

