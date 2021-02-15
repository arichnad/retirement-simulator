#!/usr/bin/python3

import csv, sys, getopt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

epsilon = 1e-6

def main(argv):
	monthly = False

	try:
		opts, args = getopt.getopt(argv,'h', ['help', 'monthly'])
	except getopt.GetoptError:
		usage()
		return
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			return
		if opt in ('--monthly'):
			monthly=True
	if len(args) < 2:
		usage()
		return
	run(float(args[0]), float(args[1])/100, monthly)

def usage():
	print('usage:  python3 simulate.py goalYears percentTakeOut')

def parse(data):
	return float(data) if data != '' else None

def withdrawalStrategy(data, bank, moneyToTakeOut):
	equityRatio = bank['equityRatio']
	
	equitiesToTakeOut = bank['equities'] - equityRatio * (getBalance(bank) - moneyToTakeOut)
	
	if equitiesToTakeOut < 0:
		#print('uneven balances (low equities):  trouble rebalancing')
		equitiesToTakeOut = 0
	
	if equitiesToTakeOut > moneyToTakeOut + epsilon:
		#print('uneven balances (high equities):  trouble rebalancing')
		equitiesToTakeOut = moneyToTakeOut
		
	if equitiesToTakeOut > bank['equities']:
		#print('low balances:  trouble rebalancing')
		equitiesToTakeOut = bank['equities']

	bondsToTakeOut = moneyToTakeOut - equitiesToTakeOut
	#print(equitiesToTakeOut, bondsToTakeOut, '', bank['equities'], bank['bonds'])
	
	bank['equities'] -= equitiesToTakeOut
	bank['bonds'] -= bondsToTakeOut

def updateBalances(data, bank):
	date = bank['date']
	
	bank['equities'] += bank['timeRatio'] * data[date]['dividends'] / data[date]['sp500'] * bank['equities']
	bank['bonds'] *= bank['timeRatio'] * data[date]['bondInterest'] + 1
	
	nextDate = date + bank['timeIncrement']
	
	bank['equities'] *= data[nextDate]['sp500'] / data[date]['sp500']
	
	bank['date'] = nextDate


def oneTimeUnit(data, bank):
	date = bank['date']

	moneyToTakeOut = bank['timeRatio'] * bank['startMoneyToTakeOut'] * data[date]['cpi'] / bank['startCpi']
	
	withdrawalStrategy(data, bank, moneyToTakeOut)

	updateBalances(data, bank)
	
	if bank['equities'] < -epsilon or bank['bonds'] < -epsilon:
		return False

	return True

def getBalance(bank):
	return bank['equities'] + bank['bonds']


def oneSimulation(data, bank, startDate, endDate, goalYears):
	good = True
	years = 0
	while good and bank['date'] < endDate and years < goalYears:
		good = oneTimeUnit(data, bank)

		years = (bank['date'] - startDate).days / 365
	
	if bank['date'] == endDate and years < goalYears:
		return None, getBalance(bank)
	
	print(startDate, 'good' if good else 'bad')
	return good, getBalance(bank)
	

def run(goalYears, percentTakeOut, monthly):
	#convert to yearly amount:
	startMoneyToTakeOut = percentTakeOut

	data = {}
	#date,s&p500,dividend,earnings,cpi
	for date,sp500,dividends,earnings,cpi,bondInterest in csv.reader(open('shiller.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y-%m')
		data[date] = {
			'sp500': parse(sp500),
			'dividends': parse(dividends),
			'earnings': parse(earnings),
			'cpi': parse(cpi),
			'bondInterest': parse(bondInterest)/100,
		}
	
	startMoney = 1
	equityRatio = 1
	startEquities = startMoney * equityRatio
	startBonds = startMoney * (1 - equityRatio)
	
	startDate=datetime(1871,1,1)
	endDate=datetime(2016,1,1)
	goodCount = 0
	totalCount = 0
	totalBalance = 0
	
	while startDate < endDate:
		bank = {
			'date': startDate,
			'equities': startEquities,
			'bonds': startBonds,
			'startCpi': data[startDate]['cpi'],
			'startMoneyToTakeOut': startMoneyToTakeOut,
			'equityRatio': equityRatio,
			'timeIncrement': relativedelta(months=1) if monthly else relativedelta(years=1),
			'timeRatio': 1/12 if monthly else 1,
		}
		good, balance = oneSimulation(data, bank, startDate, endDate, goalYears)

		if good is None: break
		
		if good:
			goodCount += 1
		totalCount += 1
		totalBalance += balance
		
		startDate+=relativedelta(months=1) if monthly else relativedelta(years=1)
	
	print('suceeded at keeping retirement money %.0f years %.0f%% of the simulations (average %.2f)' % (
		goalYears,
		goodCount / totalCount * 100,
		totalBalance / totalCount))


if __name__ == "__main__":
	main(sys.argv[1:])


