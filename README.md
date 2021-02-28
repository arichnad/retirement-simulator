retirement plan backtester
==========================

requirements
============

* python3, pip3
* argparse:  `pip3 install argparse`

usage
=====

usage: simulate.py [-h] [--verbose] [--debug YEAR] [--monthly] [--equity-percent EQUITY_PERCENT] [--tent TENT] [--extra-spending EXTRA_SPENDING]
                   [--expense-ratio EXPENSE_RATIO] [--skip-dividends]
                   goalYears start_annual_spending portfolio_size

retirement plan backtester

positional arguments:
  goalYears             number of years you want to be in retirement
  start_annual_spending
                        the money you want to spend per year, adjusted for inflation. in thousands of dollars
  portfolio_size        the starting size of the portfolio. in thousands of dollars

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         prints information about success of each scenario tested
  --debug YEAR          debug a single year
  --monthly             use "monthly" as the unit of time. default: yearly
  --equity-percent EQUITY_PERCENT
                        change the equity percentage. default: 100
  --tent TENT           use a bond tent. format: PERCENT_START,YEARS
  --extra-spending EXTRA_SPENDING
                        add extra spending. format: DOLLARS,YEARS (in thousands of dollars)
  --expense-ratio EXPENSE_RATIO
                        set the expense ratio (percent per year). default: .1
  --skip-dividends      skip inclusion of dividends. assumes dividends are always zero.


example
=======

./simulate.py --verbose --equity-percent=75 35 4 100

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

dev notes
=========

* `sed -i 's/#@profile/@profile/' simulate.py && kernprof -l ./simulate.py --monthly --equity-percent=75 35 4 100 && python3 -m line_profiler simulate.py.lprof >timing && sed -i 's/^@profile/#&/' simulate.py`
