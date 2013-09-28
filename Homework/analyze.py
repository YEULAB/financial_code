'''
@summary: Portfolio Analyzer - Read Portfolio Values File and Analyze Portfolio
'''
# Enable running in Ubuntu Server 12.10
import matplotlib
matplotlib.use('Agg')

import argparse as ap
import csv
import datetime as dt
import qstkutil.DataAccess as da
import qstkutil.qsdateutil as du
import qstkutil.tsutil as tsu
from pylab import *
import pandas
import numpy as np
import matplotlib.pyplot as plt

#
# Read program argument
# Example:
# python marketsim.py 1000000 orders.csv values.csv
argparser = ap.ArgumentParser(description="Take values file and benchmark symbol")
argparser.add_argument("valuesfile")
argparser.add_argument("benchmark")
args = argparser.parse_args()

print "Values file: " + args.valuesfile
print "Benchmark symbol: " + args.benchmark

#
# Read order file
values = []
with open(args.valuesfile, "rU") as infile:
		reader = csv.reader(infile, "excel")
		
		#read each line in value file
		for line in reader:
			values.append([dt.datetime(int(line[0]), int(line[1]), int(line[2]), 16), float(line[3])])
cash = values[0][1]

#
# Prepare to read the data
startday = values[0][0]
endday = values[-1][0]
timeofday = dt.timedelta(hours=16)
timestamps = du.getNYSEdays(startday, endday, timeofday)

#
# Read close data from symbols list
dataobj = da.DataAccess('Yahoo')
symbols = [args.benchmark]
close = dataobj.get_data(timestamps, symbols, "close", verbose=True)
close['Portfolio'] = float(0)

#
# Set Portfilio value into DataFrame
for value in values:
	close['Portfolio'][value[0]] = value[1]

#
# Prepare Data to Plot Graph
daily_price = close.values.copy()
tsu.fillforward(daily_price)
tsu.fillbackward(daily_price)
daily_price = daily_price / daily_price[0, :]
daily_price = daily_price * cash

#
# Plot Graph
plt.clf()
newtimestamps = close.index
pricedat = close.values # pull the 2D ndarray out of the pandas object
plt.plot(newtimestamps, daily_price)
plt.legend([args.benchmark, 'Portfolio'])
plt.ylabel('Value')
plt.xlabel('Date')
savefig('analyze.pdf', format='pdf')


#
# Calculate Sharpe Ratio
daily_rets = close.values.copy()
tsu.fillforward(daily_rets)
tsu.fillbackward(daily_rets)
tsu.returnize0(daily_rets)
sharpe_list = tsu.get_sharpe_ratio(daily_rets)
stdev_list =  np.std(daily_rets, axis=0)
return_list =  (daily_price[-1, :] / daily_price[0, :] - 1) * 100
print "Sharpe Ratio: " + str(sharpe_list[1])
print "Total Return: " + str(return_list[1]) + "%"
print "Standard Deviation: " + str(stdev_list[1])