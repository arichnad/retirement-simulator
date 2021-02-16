#!/usr/bin/python3

import csv, sys, getopt, copy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

epsilon = 1e-6
debug = False

def main(argv):
	monthly = False
	equityRatio = 1
	tent = None

	try:
		opts, args = getopt.getopt(argv,'h', ['help', 'monthly', 'equity-percent=', 'debug', 'tent='])
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
			equityRatio=float(arg)/100
		elif opt in ('--debug'):
			global debug
			debug=True
		elif opt in ('--tent'):
			tentPercentStart, tentYears = arg.split(',')
			tent={
				'equityRatioStart': float(tentPercentStart)/100,
				'years': float(tentYears)
			}
	if len(args) < 2:
		usage()
		return
	run(float(args[0]), float(args[1])/100, monthly, equityRatio, tent)

def usage():
	print('usage:  python3 simulate.py [--monthly] [--equity-percent=PERCENT] goalYears percentTakeOut')

def parse(data):
	return float(data) if data != '' else None

def updateCostBasis(portfolio, moneyToTakeOut):
	#avg cost basis
	costBasis = portfolio['costBasis'] * moneyToTakeOut / portfolio['balance']
	portfolio['costBasis'] -= costBasis
	#this should only go negative if we fail
	return costBasis

def withdraw(portfolio, moneyToTakeOut):
	costBasis = updateCostBasis(portfolio, moneyToTakeOut)
	portfolio['balance'] -= moneyToTakeOut

def withdrawalStrategy(data, bank, moneyToTakeOut):
	withdraw(bank['portfolio']['taxable'], moneyToTakeOut)

#def calculateBondReturn(bondInterest, nextBondInterest):
#	#not sure if this is right or not:
#	return sum((
#		bondInterest/nextBondInterest-1,
#		(1+nextBondInterest)**-119*(1-bondInterest/nextBondInterest)
#	))
	
def getEquityRatio(bank):
	tent=bank['tent']
	if tent is None:
		return bank['equityRatio']
	years = (bank['date'] - bank['startDate']).days / 365
	equityRatio = bank['equityRatio']
	if years < tent['years']:
		equityRatio = years / tent['years'] * (bank['equityRatio']-tent['equityRatioStart']) + tent['equityRatioStart']
	global debug
	if debug:
		print(equityRatio)
	return equityRatio
	
def updatePortfolio(data, bank, portfolio):
	balance = portfolio['balance']
	
	date = bank['date']
	nextDate = bank['nextDate']

	equities = getEquityRatio(bank) * balance
	bonds = balance - equities
	
	equityReturn = equities * (data[nextDate]['sp500'] / data[date]['sp500'] - 1)
	equityDividends = equities * data[date]['dividends']
	portfolio['costBasis'] += equityDividends
	
	bondDividends = bonds * data[date]['bondInterest']
	portfolio['costBasis'] += bondDividends

	#i'm not sure why we don't include the full ending balance here, but whatever
	netExpense = - sum((balance, equityReturn, bondDividends)) * bank['expenseRatio']
	portfolio['costBasis'] += -netExpense

	newBalance = sum((balance, equityReturn, equityDividends, bondDividends, netExpense))
	
	global debug
	if debug:
		print('%.3f %.3f %.3f / %.4f %.4f %.4f %.4f / %.3f %.3f' % (
			balance, equities, bonds,
			equityReturn, equityDividends, bondDividends, netExpense,
			newBalance, portfolio['costBasis']))
	
	portfolio['balance'] = newBalance

def updateBalances(data, bank):
	for portfolio in bank['portfolio'].values():
		updatePortfolio(data, bank, portfolio)


def getBalance(bank):
	return sum(portfolio['balance'] for portfolio in bank['portfolio'].values())

def oneTimeUnit(data, bank):
	date = bank['date']
	nextDate = bank['nextDate'] = date + bank['timeIncrement']
	
	moneyToTakeOut = bank['startMoneyToTakeOut'] * data[nextDate]['cpi'] / bank['startCpi']
	
	withdrawalStrategy(data, bank, moneyToTakeOut)

	updateBalances(data, bank)
	
	bank['date'] = nextDate
	
	return getBalance(bank) >= -epsilon


def oneSimulation(data, bank, goalYears):
	good = True
	years = 0
	while good and bank['date'] < bank['endDate'] and years < goalYears:
		good = oneTimeUnit(data, bank)

		years = (bank['date'] - bank['startDate']).days / 365
	
	if bank['date'] == bank['endDate'] and years < goalYears:
		return None, getBalance(bank)
	
	print(bank['startDate'], 'good' if good else 'bad')
	return good, getBalance(bank)
	

def run(goalYears, percentTakeOut, monthly, equityRatio, tent):
	#convert to yearly amount:
	timeRatio = 1/12 if monthly else 1

	data = {}
	#date,s&p500,dividend,earnings,cpi
	for date,sp500,dividends,earnings,cpi,bondInterest in csv.reader(open('shiller.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y-%m')
		data[date] = {
			'sp500': parse(sp500),
			'dividends': timeRatio * parse(dividends) / parse(sp500) if dividends != '' else None,
			'earnings': parse(earnings),
			'cpi': parse(cpi),
			'bondInterest': timeRatio * parse(bondInterest)/100,
		}
	
	startMoneyToTakeOut = timeRatio * percentTakeOut
	portfolio = {
		'taxable': {
			'balance': 1,
			'costBasis': 1,
		}
	}
	
	startDate=datetime(1871,1,1)
	endDate=datetime(2016,1,1)
	goodCount = 0
	totalCount = 0
	totalBalance = 0

	def setupBank():
		return {
			'date': startDate,
			'startDate': startDate,
			'endDate': endDate,
			'portfolio': copy.deepcopy(portfolio),
			'startCpi': data[startDate]['cpi'],
			'startMoneyToTakeOut': startMoneyToTakeOut,
			'equityRatio': equityRatio,
			'expenseRatio': timeRatio * .001,
			'timeIncrement': relativedelta(months=1) if monthly else relativedelta(years=1),
			'tent': tent,
		}

	global debug
	if debug:
		startDate = datetime(1960,1,1)
		oneSimulation(data, setupBank(), 30)
		return
	
	while startDate < endDate:
		good, balance = oneSimulation(data, setupBank(), goalYears)

		if good is None: break
		
		if good:
			goodCount += 1
		totalCount += 1
		totalBalance += balance
		
		startDate+=relativedelta(months=1) if monthly else relativedelta(years=1)
	
	print('equity %-3d%%, bond %-3d%%, %s%.0f years: success %.1f%% of the simulations (average ending balance %.3f)' % (
		round(equityRatio*100),
		round((1-equityRatio)*100),
		'tent %d,%d, ' % (
			round(tent['equityRatioStart']*100), tent['years']
		) if tent else '',
		goalYears,
		goodCount / totalCount * 100,
		totalBalance / totalCount))


if __name__ == "__main__":
	main(sys.argv[1:])


