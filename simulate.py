#!/usr/bin/python3

import csv, sys, getopt, copy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

epsilon = 1e-6
debugYear = None
verbose = False

def main(argv):
	monthly = False
	equityRatio = 1
	tent = None
	expenseRatio = .001
	skipDividends = False

	try:
		opts, args = getopt.getopt(argv,'h', ['help', 'monthly', 'equity-percent=', 'tent=', 'debug=', 'expenseRatio=', 'skipDividends', 'verbose'])
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
			global debugYear
			print('balance equities bonds / equityReturn equityDividends bondDividends netExpense / newBalance costBasis')
			debugYear=int(arg)
		elif opt in ('--verbose'):
			global verbose
			verbose = True
		elif opt in ('--tent'):
			tentPercentStart, tentYears = arg.split(',')
			tent={
				'equityRatioStart': float(tentPercentStart)/100,
				'years': float(tentYears)
			}
		elif opt in ('--expenseRatio'):
			expenseRatio = float(arg)/100
		elif opt in ('--skipDividends'):
			skipDividends = True
	if len(args) < 3:
		usage()
		return
	run(float(args[0]), float(args[1]), float(args[2]), monthly, equityRatio, tent, expenseRatio, skipDividends)

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

def withdraw(portfolio, spending):
	costBasis = updateCostBasis(portfolio, spending)
	portfolio['balance'] -= spending 

def withdrawalStrategy(data, bank, spending):
	withdraw(bank['portfolio']['taxable'], spending)

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
	return equityRatio
	
def updatePortfolio(data, bank, portfolio):
	balance = portfolio['balance']
	
	date = bank['date']
	nextDate = bank['nextDate']

	equities = getEquityRatio(bank) * balance
	bonds = balance - equities
	
	equityReturn = equities * (data[nextDate]['sp500'] / data[date]['sp500'] - 1)
	equityDividends = equities * data[date]['dividends']
	
	bondDividends = bonds * data[date]['bondInterest']

	#i'm not sure why we don't include the full ending balance here, but whatever
	netExpense = - sum((balance, equityReturn, bondDividends)) * bank['expenseRatio']

	newBalance = sum((balance, equityReturn, equityDividends, bondDividends, netExpense))
	portfolio['costBasis'] += sum((equityDividends, bondDividends, -netExpense))
	
	global debugYear
	if debugYear is not None:
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
	
	spending = bank['startSpending'] * data[nextDate]['cpi'] / bank['startCpi']
	
	withdrawalStrategy(data, bank, spending)

	updateBalances(data, bank)
	
	bank['date'] = nextDate
	
	return getBalance(bank) >= -epsilon


def oneSimulation(data, bank, goalYears):
	good = True
	years = 0
	while good and bank['date'] < bank['endDate'] and years < goalYears:
		good = oneTimeUnit(data, bank)

		years = (bank['date'] - bank['startDate']).days / 365
	
	if bank['date'] >= bank['endDate']:
		return None, None
	
	global verbose
	if verbose:
		print(bank['startDate'], 'good' if good else 'bad')
	return good, getBalance(bank)
	

def run(goalYears, startAnnualSpending, portfolioSize, monthly, equityRatio, tent, expenseRatio, skipDividends):
	#convert to yearly amount:
	timeRatio = 1/12 if monthly else 1

	data = {}
	#date,s&p500,dividend,earnings,cpi
	for date,sp500,dividends,earnings,cpi,bondInterest in csv.reader(open('shiller.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y-%m')
		dividends = (parse(dividends) / parse(sp500) + 1) ** timeRatio - 1 if dividends != '' and not skipDividends else 0
		data[date] = {
			'sp500': parse(sp500),
			'dividends': dividends,
			'earnings': parse(earnings),
			'cpi': parse(cpi),
			'bondInterest': (parse(bondInterest)/100 + 1) ** timeRatio - 1,
		}
	
	startSpending = startAnnualSpending * timeRatio
	portfolio = {
		'taxable': {
			'balance': portfolioSize,
			'costBasis': portfolioSize,
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
			'startSpending': startSpending,
			'equityRatio': equityRatio,
			'expenseRatio': (expenseRatio + 1) ** timeRatio - 1,
			'timeIncrement': relativedelta(months=1) if monthly else relativedelta(years=1),
			'tent': tent,
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


