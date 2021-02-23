#!/bin/bash

set -e #exit on failure

cd ..

#regenerateOutputs=yes

start=$(date +%s)


echo yearly
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --verbose 40 .04 1 >unit-tests/40-4-yearly
./simulate.py --verbose 40 .04 1 |diff -u unit-tests/40-4-yearly -

echo 75 percent equity
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --equity-percent=75 --verbose 40 .04 1 >unit-tests/40-4-75
./simulate.py --equity-percent=75 --verbose 40 .04 1 |diff -u unit-tests/40-4-75 -

echo 75 percent equity extra spending
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --equity-percent=75 --extra-spending=.04,100 --verbose 40 0 1 >unit-tests/40-4-75-extra
./simulate.py --equity-percent=75 --extra-spending=.04,100 --verbose 40 0 1 |diff -u unit-tests/40-4-75-extra -

echo tent
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --equity-percent=75 --tent=45,20 --verbose 40 .04 1 >unit-tests/40-4-75-tent
./simulate.py --equity-percent=75 --tent=45,20 --verbose 40 .04 1 |diff -u unit-tests/40-4-75-tent -

echo 1960 debug
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --equity-percent=75 --debug=1960 --verbose 30 .04 1 >unit-tests/1960-debug
./simulate.py --equity-percent=75 --debug=1960 --verbose 30 .04 1 |diff -u unit-tests/1960-debug -

echo 1990 debug
echo 1123.59/339.97 = 3.305
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --monthly --equity-percent=100 --debug=1990 --skipDividends --expenseRatio=0 --verbose 20 0 1 >unit-tests/1990-debug
./simulate.py --monthly --equity-percent=100 --debug=1990 --skipDividends --expenseRatio=0 --verbose 20 0 1 |diff -u unit-tests/1990-debug -

echo monthly
[ "$regenerateOutputs" == 'yes' ] && ./simulate.py --monthly --verbose 40 .04 1 >unit-tests/40-4-monthly
./simulate.py --monthly --verbose 40 .04 1 |diff -u unit-tests/40-4-monthly -

runtime=$(($(date +%s)-start))

echo SUCCESS $runtime

