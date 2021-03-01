#!/usr/bin/python3

import csv, sys, copy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import argparse

epsilon = 1e-6
debugYear = None
verbose = False

MIN_DATA_START=1871
MAX_DATA_END=2021

DEFAULT_DATA_END=2016

def checkDataStart(year):
	year=int(year)
	if year < MIN_DATA_START:
		raise argparse.ArgumentTypeError("%d is before the start year of %d" % (year, MIN_DATA_START))
	return year

def checkDataEnd(year):
	year=int(year)
	if year > MAX_DATA_END:
		raise argparse.ArgumentTypeError("%d is after the end year of %d" % (year, MAX_DATA_END))
	return year

def getTent(arg):
	tentPercentStart, tentYears = arg.split(',')
	return {
		'equityRatioStart': float(tentPercentStart)/100,
		'years': float(tentYears)
	}

def getExtraSpending(arg):
	extraSpendingAmount, extraSpendingYears = arg.split(',')
	return {
		'amount': float(extraSpendingAmount),
		'years': float(extraSpendingYears),
		'real': False,
	}

def main():
	parser = argparse.ArgumentParser(description = 'retirement plan backtester')
	parser.set_defaults(func=lambda args: parser.print_help())
	
	parser.add_argument('--verbose', '-v', action='store_true',
    	help='prints information about success of each scenario tested')
	
	parser.add_argument('--debug', type=int, metavar='YEAR',
    	help='debug a single year')
	
	parser.add_argument('--monthly', action='store_true',
		help='use "monthly" as the unit of time.  default:  yearly')
	
	parser.add_argument('--equity-percent', type=float, default=100,
		help='change the equity percentage.  default:  100')
	
	parser.add_argument('--tent', type=getTent,
		help='use a bond tent.  format:  PERCENT_START,YEARS')
	
	parser.add_argument('--extra-spending', type=getExtraSpending,
		help='add extra spending.  format:  DOLLARS,YEARS (in thousands of dollars)')
	
	parser.add_argument('--expense-ratio', type=float, default=.1,
		help='set the expense ratio (percent per year).  default: .1')
	
	parser.add_argument('--data-start', type=checkDataStart, default=MIN_DATA_START,
		help='simulations start on or after this year.  do not pick anything before %d' % MIN_DATA_START)
	
	parser.add_argument('--data-end', type=checkDataEnd, default=DEFAULT_DATA_END,
		help='simulations end on or before this year.  do not pick anything after %d' % MAX_DATA_END)
	
	parser.add_argument('--skip-dividends', action='store_true',
		help='skip inclusion of dividends.  assumes dividends are always zero.')
	
	parser.add_argument('goalYears', type=float,
		help='number of years you want to be in retirement')
	
	parser.add_argument('start_annual_spending', type=float,
		help='the money you want to spend per year, adjusted for inflation.  in thousands of dollars')
	
	parser.add_argument('portfolio_size', type=float,
		help='the starting size of the portfolio.  in thousands of dollars')
	
	args = parser.parse_args()

	global verbose
	verbose = args.verbose
	bank = {
		'dataStart': datetime(args.data_start, 1, 1),
		'dataEnd': datetime(args.data_end, 1, 1),
		'startSpending': args.start_annual_spending,
		'portfolio': {
			'taxable': {
				'balance': args.portfolio_size,
				'costBasis': args.portfolio_size,
			}
		},
		'expenseRatio': args.expense_ratio/100,
		'tent': args.tent,
		'extraSpending': args.extra_spending,
		'equityRatio': args.equity_percent/100,
	}

	if args.debug is not None:
		global debugYear
		debugYear=int(args.debug)
		print('balance / spending capitalGainsTax / equities bonds / equityReturn equityDividends bondDividends netExpense / newBalance costBasis')
	
	bank = adjustDueToTime(bank, args.monthly)

	run(bank, float(args.goalYears), args.monthly, args.skip_dividends)

def parse(data):
	return float(data) if data != '' else None

def updateCostBasis(portfolio, spending):
	#avg cost basis
	costBasis = portfolio['costBasis'] * spending / portfolio['balance']
	portfolio['costBasis'] -= costBasis
	#this should only go negative if we fail
	return costBasis

def calculateCapitalGains(portfolio, spending):
	capitalGainsTax = 0

	return capitalGainsTax

#@profile
def withdraw(portfolio, spending):
	capitalGainsTax = calculateCapitalGains(portfolio, spending)
	
	global debugYear
	if debugYear is not None:
		print('%.3f / %.3f %.3f / ' % (
			portfolio['balance'], -spending, -capitalGainsTax,
			), end='')

	spendingWithTaxes = sum((spending, capitalGainsTax))

	updateCostBasis(portfolio, spendingWithTaxes)
	portfolio['balance'] -= spendingWithTaxes

def withdrawalStrategy(data, bank, spending):
	withdraw(bank['portfolio']['taxable'], spending)

#def calculateBondReturn(bondInterest, nextBondInterest):
#	#not sure if this is right or not:
#	return sum((
#		bondInterest/nextBondInterest-1,
#		(1+nextBondInterest)**-119*(1-bondInterest/nextBondInterest)
#	))
	
def getYears(bank):
	return (bank['date'] - bank['start']).days / 365

def getEquityRatio(bank):
	tent=bank['tent']
	if tent is None:
		return bank['equityRatio']
	equityRatio = bank['equityRatio']
	years = getYears(bank)
	if years < tent['years']:
		equityRatio = years / tent['years'] * (bank['equityRatio']-tent['equityRatioStart']) + tent['equityRatioStart']
	return equityRatio
	
#@profile
def updatePortfolio(data, bank, portfolio):
	balance = portfolio['balance']
	
	date = bank['date']

	equities = getEquityRatio(bank) * balance
	bonds = balance - equities
	
	equityReturn = equities * data[date]['sp500Increase']
	equityDividends = equities * data[date]['dividends']
	
	bondDividends = bonds * data[date]['bondInterest']

	#i'm not sure why we don't include the full ending balance here, but whatever
	netExpense = - sum((balance, equityReturn, bondDividends)) * bank['expenseRatio']

	newBalance = sum((balance, equityReturn, equityDividends, bondDividends, netExpense))
	portfolio['costBasis'] += sum((equityDividends, bondDividends, -netExpense))
	
	global debugYear
	if debugYear is not None:
		print('%.3f %.3f / %.4f %.4f %.4f %.4f / %.3f %.3f' % (
			equities, bonds,
			equityReturn, equityDividends, bondDividends, netExpense,
			newBalance, portfolio['costBasis']))
	
	portfolio['balance'] = newBalance

def updateBalances(data, bank):
	for portfolio in bank['portfolio'].values():
		updatePortfolio(data, bank, portfolio)


def getBalance(bank):
	return sum(portfolio['balance'] for portfolio in bank['portfolio'].values())

def getSpending(data, bank):
	inflation = data[bank['date']]['nextCpi'] / bank['startCpi']

	spending = bank['startSpending'] * inflation
	if bank['extraSpending'] is not None and getYears(bank) < bank['extraSpending']['years']:
		extraSpending = bank['extraSpending']['amount']
		if bank['extraSpending']['real']:
			extraSpending *= inflation
		spending += extraSpending
	
	return spending

#@profile
def oneTimeUnit(data, bank):
	withdrawalStrategy(data, bank, getSpending(data, bank))

	updateBalances(data, bank)
	
	bank['date'] = data[bank['date']]['nextDate']
	
	return getBalance(bank) >= -epsilon


#@profile
def oneSimulation(data, bank, goalYears):
	good = True
	
	while bank['date'] < bank['end'] and getYears(bank) < goalYears:
		good = oneTimeUnit(data, bank)
	
	if bank['date'] >= bank['end']:
		return None, None
	
	global verbose
	if verbose:
		print(bank['start'], 'good' if good else 'bad')

	balanceAdjusted = getBalance(bank) / data[bank['date']]['cpi'] * bank['startCpi']
	return good, balanceAdjusted

def adjustExtraSpending(extraSpending, timeRatio):
	if extraSpending is None:
		return None
	return {
		**extraSpending,
		'amount': extraSpending['amount'] * timeRatio,
	}

def getTimeRatio(monthly):
	return 1/12 if monthly else 1

def adjustDueToTime(bank, monthly):
	timeRatio = getTimeRatio(monthly)
	return {
		**bank,
		'startSpending': bank['startSpending'] * timeRatio,
		'expenseRatio': (bank['expenseRatio'] + 1) ** timeRatio - 1,
		'extraSpending': adjustExtraSpending(bank['extraSpending'], timeRatio),
	}

#@profile
def run(bank, goalYears, monthly, skipDividends):
	timeRatio = getTimeRatio(monthly)
	timeIncrement = relativedelta(months=1) if monthly else relativedelta(years=1)

	data = {}
	#date,s&p500,dividend,earnings,cpi
	for date,sp500,dividends,earnings,cpi,bondInterest in csv.reader(open('shiller.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y-%m')
		dividends = (parse(dividends) / parse(sp500) + 1) ** timeRatio - 1 if dividends != '' and not skipDividends else 0
		data[date] = {
			'nextDate': date + timeIncrement,
			'sp500': parse(sp500),
			'dividends': dividends,
			'earnings': parse(earnings),
			'cpi': parse(cpi),
			'bondInterest': (parse(bondInterest)/100 + 1) ** timeRatio - 1,
		}
	
	for dataEntry in data.values():
		nextDate = dataEntry['nextDate']
		if nextDate not in data:
			break
		dataEntry['sp500Increase'] = data[nextDate]['sp500'] / dataEntry['sp500'] - 1
		dataEntry['nextCpi'] = data[nextDate]['cpi']
	
	goodCount = 0
	totalCount = 0
	totalBalance = 0

	def setupBank():
		return {
			**bank,
			'start': start,
			'end': end,
			'date': start,
			'portfolio': copy.deepcopy(bank['portfolio']),
			'startCpi': data[start]['cpi'],
		}

	start = bank['dataStart']
	end = bank['dataEnd']
	
	global debugYear
	if debugYear is not None:
		start = datetime(debugYear,1,1)
		oneSimulation(data, setupBank(), goalYears)
		return
	
	while start < end:
		good, balance = oneSimulation(data, setupBank(), goalYears)

		if good is None: break
		
		if good:
			goodCount += 1
		totalCount += 1
		totalBalance += balance
		
		start = data[start]['nextDate']
	
	print('equity %-3d%%, bond %-3d%%, %s%.0f years: success %.1f%% of the simulations (average ending balance %.3f)' % (
		round(bank['equityRatio']*100),
		round((1-bank['equityRatio'])*100),
		'tent %d,%d, ' % (
			round(bank['tent']['equityRatioStart']*100), bank['tent']['years']
		) if bank['tent'] else '',
		goalYears,
		goodCount / totalCount * 100,
		totalBalance / totalCount))


if __name__ == "__main__":
	main()


