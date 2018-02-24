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
	doInvest=True
	doInflation=True
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			return
		if opt in ('--no-invest'):
			doInvest=False
		if opt in ('--no-inflation'):
			doInflation=False
	if len(args) < 2:
		usage()
		return
	run(float(args[0]), float(args[1]), doInvest, doInflation)

def usage():
	print('usage:  python3 simulate.py [--no-invest] [--no-inflation] goalYears percentTakeOut')

def parse(data):
	return float(data) if data != '' else None

def oneSimulation(data, startDate, endDate, goalYears, startMoneyToTakeOut, doInvest, doInflation):
	date=startDate
	startCpi=data[date]['cpi']
	#the only reason to track "shares" istead of "money" is you don't have to look at previous rows
	shares=1/data[date]['sp500'] if doInvest else 1
	good = False
	while date < endDate:
		moneyToTakeOut = startMoneyToTakeOut * (data[date]['cpi'] / startCpi if doInflation else 1)
		
		sharesToTakeOut = moneyToTakeOut / ( data[date]['sp500'] if doInvest else 1 )

		shares -= sharesToTakeOut
		
		shares += data[date]['dividends'] / data[date]['sp500'] * shares if doInvest else 0
		
		#print(moneyToTakeOut, sharesToTakeOut, shares)
		if shares < 0: break
		date+=relativedelta(years=1)
		years = (date - startDate).days / 365
		if years >= goalYears:
			good = True
			break
	
	if not good and date == endDate:
		return None
	
	print(startDate, 'good' if good else 'bad')
	return good
	

def run(goalYears, percentTakeOut, doInvest, doInflation):
	#convert to yearly amount:
	startMoneyToTakeOut = percentTakeOut/100

	data={}
	#year,s&p500,dividends,earnings,interest rate,long government bond,cpi
	for date,sp500,dividends,earnings,interest,governmentBond,cpi in csv.reader(open('shiller.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y')
		data[date]={'sp500': parse(sp500), 'dividends': parse(dividends), 'earnings': parse(earnings), \
				'interest': parse(interest), 'governmentBond': parse(governmentBond), 'cpi': parse(cpi)}
	
	startDate=datetime(1871,1,1)
	endDate=datetime(2016,1,1)
	goodCount = 0
	totalCount = 0
	while startDate < endDate:
		good = oneSimulation(data, startDate, endDate, goalYears, startMoneyToTakeOut, doInvest, doInflation)

		if good is None: break

		if good:
			goodCount += 1
		
		totalCount += 1
		
		startDate+=relativedelta(years=1)
	print('suceeded at keeping retirement money %.0f years %.0f%% of the simulations' % (goalYears, goodCount / totalCount * 100))


if __name__ == "__main__":
	main(sys.argv[1:])


