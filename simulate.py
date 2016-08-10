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

def run(goalYears, percentTakeOut, doInvest, doInflation):
	#convert to monthly amount:
	startMoneyToTakeOut = percentTakeOut/100/12

	cpi={}
	djia={}
	for date, value in csv.reader(open('cpi.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y-%m-%d')
		cpi[date]=float(value)
	for date, value in csv.reader(open('djia.csv', 'r')):
		if date.lower() == 'date': continue
		date=datetime.strptime(date,'%Y-%m-%d')
		date=datetime(date.year, date.month, 1) #shift to the 1st, so keys will work
		djia[date]=float(value)
	
	startDate=datetime(1947,1,1)
	endDate=datetime(2016,4,1)
	goodCount = 0
	totalCount = 0
	while startDate < endDate:
		date=startDate
		startCpi=cpi[date]
		shares=1/djia[date] if doInvest else 1
		good = False
		while date < endDate:
			moneyToTakeOut = startMoneyToTakeOut * (cpi[date] / startCpi if doInflation else 1)
			
			sharesToTakeOut = moneyToTakeOut / ( djia[date] if doInvest else 1 )

			shares -= sharesToTakeOut
			#print(moneyToTakeOut, sharesToTakeOut, shares)
			if shares < 0: break
			date+=relativedelta(months=1)
			years = (date - startDate).days / 365
			if years >= goalYears:
				goodCount += 1
				good = True
				break
		
		if not good and date == endDate:
			break
		totalCount += 1
		print(startDate, 'good' if good else 'bad')
		
		startDate+=relativedelta(months=1)
	print('suceeded at keeping retirement money %.0f years %.0f%% of the simulations' % (goalYears, goodCount / totalCount * 100))


if __name__ == "__main__":
	main(sys.argv[1:])


