a simulator for retirement.
===========================

usage
=====

python3 simulate.py [--no-invest] [--no-inflation] goalYears percentTakeOut

example
=======

python3 simulate.py 33 4

* All money is placed in an investment that follows the [S&P 500 index](https://en.wikipedia.org/wiki/S%26P_500_Index).

* This above example states you want retirement money to last 33 years or longer

* The example also states you want to want to take out 4 % per year (divided per month) [adjusted for inflation](https://en.wikipedia.org/wiki/Consumer_price_index).

* Will run between 1947 and 2016 and tell you which retirement start times will succeed and which will fail.

data
====

* [uses S&P 500 and CPI data from here](http://www.econ.yale.edu/~shiller/data.htm)

