a simulator for retirement.
===========================

usage
=====

python3 simulate.py [--monthly] [--equity-percent=PERCENT] goalYears percentTakeOut

example
=======

python3 simulate.py --equity-percent=75 35 4

* 75% of the money is placed in an investment that follows the [S&P 500 index](https://en.wikipedia.org/wiki/S%26P_500_Index).

* 25% of the money is placed in an investment that follows government bond rates.

* Rebalancing happens yearly.

* Uses a hard-coded expense ratio of 0.1%/year.

* This above example states you want retirement money to last 35 years or longer.

* The example also states you want to want to take out 4% of your starting balance per year [adjusted for inflation](https://en.wikipedia.org/wiki/Consumer_price_index).

* Will run between 1871 and 2016 and tell you which retirement start times will succeed and which will fail.

data
====

* [uses S&P 500 and CPI data from here](http://www.econ.yale.edu/~shiller/data.htm)

	* [specifically this spreadsheet](http://www.econ.yale.edu/~shiller/data/ie_data.xls)

`(echo 'date,s&p500,dividend,earnings,cpi,bondInterest'; cat shiller-raw.tsv |egrep '^[0-9]' |cut -f1-5,7 |sed -e 's/\./-/' -e 's/\t/,/g' -e 's/-1,/-10,/g') >shiller.csv`

* output data was compared to firecalc.com

