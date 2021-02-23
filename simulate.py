#!/usr/bin/python3

import csv, sys, getopt, copy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

epsilon = 1e-6
debugYear = None
verbose = False

def main(argv):
	monthly = False
	skipDividends = False
	bank = {
		'equityRatio': 1,
		'tent': None,
		'extraSpending': None,
		'expenseRatio': .001,
	}

	try:
		opts, args = getopt.getopt(argv,'h', ['help', 'monthly', 'equity-percent=', 'tent=', 'extra-spending=', 'debug=', 'expenseRatio=', 'skipDividends', 'verbose'])
	except getopt.GetoptError:
		usage()
		return
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			return
		elif opt in ('--monthly'):
			monthly=True
		elif opt in ('--equity-percent'):
			bank['equityRatio']=float(arg)/100
		elif opt in ('--debug'):
			global debugYear
			print('balance / spending capitalGainsTax / equities bonds / equityReturn equityDividends bondDividends netExpense / newBalance costBasis')
			debugYear=int(arg)
		elif opt in ('--verbose'):
			global verbose
			verbose = True
		elif opt in ('--tent'):
			tentPercentStart, tentYears = arg.split(',')
			bank['tent']={
				'equityRatioStart': float(tentPercentStart)/100,
				'years': float(tentYears)
			}
		elif opt in ('--extra-spending'):
			extraSpendingAmount, extraSpendingYears = arg.split(',')
			bank['extraSpending']={
				'amount': float(extraSpendingAmount),
				'years': float(extraSpendingYears),
				'real': False,
			}
		elif opt in ('--expenseRatio'):
			bank['expenseRatio'] = float(arg)/100
		elif opt in ('--skipDividends'):
			skipDividends = True
	if len(args) < 3:
		usage()
		return
	
	bank['startSpending'] = float(args[1])
	bank['portfolio'] = {
		'taxable': {
			'balance': float(args[2]),
			'costBasis': float(args[2]),
		}
	}
	bank = adjustDueToTime(bank, monthly)

	run(bank, float(args[0]), monthly, skipDividends)

def usage():
	print('usage:  python3 simulate.py [--monthly] [--verbose] [--equity-percent=PERCENT] goalYears startAnnualSpending portfolioSize')

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
	return (bank['date'] - bank['startDate']).days / 365

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
	
	while good and bank['date'] < bank['endDate'] and getYears(bank) < goalYears:
		good = oneTimeUnit(data, bank)
	
	if bank['date'] >= bank['endDate']:
		return None, None
	
	global verbose
	if verbose:
		print(bank['startDate'], 'good' if good else 'bad')
	return good, getBalance(bank)

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
	
	startDate=datetime(1871,1,1)
	endDate=datetime(2016,1,1)
	goodCount = 0
	totalCount = 0
	totalBalance = 0

	def setupBank():
		return {
			**bank,
			'date': startDate,
			'startDate': startDate,
			'endDate': endDate,
			'portfolio': copy.deepcopy(bank['portfolio']),
			'startCpi': data[startDate]['cpi'],
		}

	global debugYear
	if debugYear is not None:
		startDate = datetime(debugYear,1,1)
		oneSimulation(data, setupBank(), goalYears)
		return
	
	while startDate < endDate:
		good, balance = oneSimulation(data, setupBank(), goalYears)

		if good is None: break
		
		if good:
			goodCount += 1
		totalCount += 1
		totalBalance += balance
		
		startDate = data[startDate]['nextDate']
	
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
	main(sys.argv[1:])


