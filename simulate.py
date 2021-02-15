#!/usr/bin/python3

import csv, sys, getopt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def main(argv):
	try:
		opts, args = getopt.getopt(argv,'h', ['help', 'no-invest', 'no-inflation'])
	except getopt.GetoptError:
		usage()
		return
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			return
	if len(args) < 2:
		usage()
		return
	run(float(args[0]), float(args[1]))

def usage():
	print('usage:  python3 simulate.py goalYears percentTakeOut')

def parse(data):
	return float(data) if data != '' else None

def oneTimeUnit(data, bank):
	date = bank['date']

	moneyToTakeOut = bank['startMoneyToTakeOut'] * data[date]['cpi'] / bank['startCpi']
	
	sharesToTakeOut = moneyToTakeOut / data[date]['sp500']

	bank['shares'] -= sharesToTakeOut
	
	bank['shares'] += data[date]['dividends'] / data[date]['sp500'] * bank['shares']
	
	#print(moneyToTakeOut, sharesToTakeOut, bank['shares'])
	if bank['shares'] < 0:
		return False

	bank['date']+=relativedelta(years=1)

	return True

	

def oneSimulation(data, bank, startDate, endDate, goalYears):
	good = True
	years = 0
	while good and bank['date'] < endDate and years < goalYears:
		good = oneTimeUnit(data, bank)

		years = (bank['date'] - startDate).days / 365
	
	if bank['date'] == endDate and years < goalYears:
		return None, bank['shares']
	
	print(startDate, 'good' if good else 'bad')
	return good, bank['shares']
	

def run(goalYears, percentTakeOut):
	#convert to yearly amount:
	startMoneyToTakeOut = percentTakeOut/100

	data = {}
	#date,s&p500,dividend,earnings,cpi
	for date,sp500,dividends,earnings,cpi,bondInterest in csv.reader(open('shiller.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y')
		data[date] = {
			'sp500': parse(sp500),
			'dividends': parse(dividends),
			'earnings': parse(earnings),
			'cpi': parse(cpi),
			'bondInterest': parse(bondInterest)/100,
		}
	
	startDate=datetime(1871,1,1)
	endDate=datetime(2016,1,1)
	goodCount = 0
	totalCount = 0
	totalBalance = 0
	
	while startDate < endDate:
		#the only reason to track "shares" istead of "money" is you don't have to look at previous rows
		bank = {
			'date': startDate,
			'shares': 1/data[startDate]['sp500'],
			'startCpi': data[startDate]['cpi'],
			'startMoneyToTakeOut': startMoneyToTakeOut,
		}
		good, balance = oneSimulation(data, bank, startDate, endDate, goalYears)

		if good is None: break
		
		if good:
			goodCount += 1
		totalCount += 1
		totalBalance += balance
		
		startDate+=relativedelta(years=1)
	
	print('suceeded at keeping retirement money %.0f years %.0f%% of the simulations (average %.2f)' % (
		goalYears,
		goodCount / totalCount * 100,
		totalBalance / totalCount))


if __name__ == "__main__":
	main(sys.argv[1:])


