a simulator for retirement.
===========================

usage
=====

python3 simulate.py [--no-invest] [--no-inflation] goalYears percentTakeOut

example
=======

python3 simulate.py 33 4

* All money is placed in an investment that follows the [Dow Jones Industrial Average](https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average).

* This above example states you want retirement money to last 33 years or longer

* The example also states you want to want to take out 4 % per year (divided per month) [adjusted for inflation](https://en.wikipedia.org/wiki/Consumer_price_index).

* Will run between 1947 and 2016 and tell you which retirement start times will succeed and which will fail.

data
====

* [uses CPI data from here](https://www.quandl.com/api/v3/datasets/FRED/CPIAUCSL.csv)

* [Uses DJIA data from here](https://www.quandl.com/api/v3/datasets/BCB/UDJIAD1.csv)

