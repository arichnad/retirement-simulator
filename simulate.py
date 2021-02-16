#!/usr/bin/python3

import csv, sys, getopt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

epsilon = 1e-6

def main(argv):
	monthly = False
	equityRatio = 1

	try:
		opts, args = getopt.getopt(argv,'h', ['help', 'monthly', 'equity-ratio='])
	except getopt.GetoptError:
		usage()
		return
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			return
		if opt in ('--monthly'):
			monthly=True
		if opt in ('--equity-ratio'):
			equityRatio=float(arg)
	if len(args) < 2:
		usage()
		return
	run(float(args[0]), float(args[1])/100, monthly, equityRatio)

def usage():
	print('usage:  python3 simulate.py [--equity-ratio=RATIO] goalYears percentTakeOut')

def parse(data):
	return float(data) if data != '' else None

def withdrawalStrategy(data, bank, moneyToTakeOut):
	bank['portfolio'] -= moneyToTakeOut

def calculateBondReturn(bondInterest, nextBondInterest):
	#this is what other websites use:
	return bondInterest

	#not sure if this is right or not:
	#return sum((
	#	bondInterest/nextBondInterest,
	#	bondInterest,
	#	(1+nextBondInterest)**-119*(1-bondInterest/nextBondInterest)
	#))

def updateBalances(data, bank):
	date = bank['date']
	nextDate = bank['nextDate']
	
	equities = bank['equityRatio'] * bank['portfolio']
	bonds = bank['portfolio'] - equities
	
	equities = equities * sum((data[nextDate]['sp500'], data[date]['dividends'])) / data[date]['sp500']
	
	bonds += bonds * calculateBondReturn(data[date]['bondInterest'], data[nextDate]['bondInterest'])

	bank['portfolio'] = equities + bonds


def oneTimeUnit(data, bank):
	date = bank['date']
	nextDate = bank['nextDate'] = date + bank['timeIncrement']
	
	moneyToTakeOut = bank['startMoneyToTakeOut'] * data[nextDate]['cpi'] / bank['startCpi']
	
	withdrawalStrategy(data, bank, moneyToTakeOut)

	updateBalances(data, bank)
	
	bank['date'] = nextDate
	
	return bank['portfolio'] >= -epsilon


def oneSimulation(data, bank, startDate, endDate, goalYears):
	good = True
	years = 0
	while good and bank['date'] < endDate and years < goalYears:
		good = oneTimeUnit(data, bank)

		years = (bank['date'] - startDate).days / 365
	
	if bank['date'] == endDate and years < goalYears:
		return None, bank['portfolio']
	
	print(startDate, 'good' if good else 'bad')
	return good, bank['portfolio']
	

def run(goalYears, percentTakeOut, monthly, equityRatio):
	#convert to yearly amount:
	timeRatio = 1/12 if monthly else 1

	data = {}
	#date,s&p500,dividend,earnings,cpi
	for date,sp500,dividends,earnings,cpi,bondInterest in csv.reader(open('shiller.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y-%m')
		data[date] = {
			'sp500': parse(sp500),
			'dividends': timeRatio * parse(dividends) if dividends != '' else None,
			'earnings': parse(earnings),
			'cpi': parse(cpi),
			'bondInterest': timeRatio * parse(bondInterest)/100,
		}
	
	startMoneyToTakeOut = timeRatio * percentTakeOut
	portfolio = 1
	
	startDate=datetime(1871,1,1)
	endDate=datetime(2016,1,1)
	goodCount = 0
	totalCount = 0
	totalBalance = 0
	
	while startDate < endDate:
		bank = {
			'date': startDate,
			'portfolio': portfolio,
			'startCpi': data[startDate]['cpi'],
			'startMoneyToTakeOut': startMoneyToTakeOut,
			'equityRatio': equityRatio,
			'timeIncrement': relativedelta(months=1) if monthly else relativedelta(years=1),
		}
		good, balance = oneSimulation(data, bank, startDate, endDate, goalYears)

		if good is None: break
		
		if good:
			goodCount += 1
		totalCount += 1
		totalBalance += balance
		
		startDate+=relativedelta(months=1) if monthly else relativedelta(years=1)
	
	print('equity %-3d%%, bond %-3d%%, %.0f years: success %.1f%% of the simulations (average %.3f)' % (
		round(equityRatio*100),
		round((1-equityRatio)*100),
		goalYears,
		goodCount / totalCount * 100,
		totalBalance / totalCount))


if __name__ == "__main__":
	main(sys.argv[1:])


