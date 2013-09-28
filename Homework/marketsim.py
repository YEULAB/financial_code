'''
@summary: Market Simulator - Read Order and Calculate Portfolio values
'''
# Enable running in Ubuntu Server 12.10
import matplotlib
matplotlib.use('Agg')

import argparse as ap
import csv
import datetime as dt
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
from pylab import *
import pandas
import numpy as np

#
# Read program argument
# Example:
# python marketsim.py 1000000 orders.csv values.csv
argparser = ap.ArgumentParser(description="Take cash, order file and output values file.")
argparser.add_argument("cash", type=float)
argparser.add_argument("orderfile")
argparser.add_argument("outputfile")
args = argparser.parse_args()

print "Starting cash: " + str(args.cash)
print "Order file: " + args.orderfile
print "Output file: " + args.outputfile

#
# Read order file
orders = []
with open(args.orderfile, "rU") as infile:
		reader = csv.reader(infile, "excel")
		
		#read each line in order file
		for line in reader:
			orders.append([dt.datetime(int(line[0]), int(line[1]), int(line[2]), 16), line[3], line[4], int(line[5])])

#
# Prepare to read the data
orders = sorted(orders)
startday = orders[0][0]
endday = orders[-1][0]
timeofday = dt.timedelta(hours=16)
timestamps = du.getNYSEdays(startday, endday, timeofday)

#
#Read close data from symbols list
dataobj = da.DataAccess('Yahoo')
symbols = list(set([order[1] for order in orders]))
close = dataobj.get_data(timestamps, symbols, "close", verbose=True)

position = close * 0
position['cash'] = float(0)

for order in orders:
	qty = order[3] if order[2] == "Buy" else -order[3]
	price = close[order[1]][order[0]]
	position[order[1]][order[0]] = position[order[1]][order[0]] + qty
	position['cash'][order[0]] = position['cash'][order[0]] - (qty * price)

for i in range(1, len(position.index)):
	position.ix[i] = position.ix[i] + position.ix[i - 1]

position['value'] = sum(position.ix[:, :-1] * close, axis=1) + position['cash'] + 1000000

with open(args.outputfile, "w") as outfile:
	writer = csv.writer(outfile)

	for index in position.index:
		writer.writerow([index.year, index.month, index.day, position['value'][index]])