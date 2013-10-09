'''
Run code as follows:
	python Backtester.py <price> 2008-01-01 2012-12-31 sp5002012 orders.csv
'''
# Enable running in Ubuntu Server 12.10
import matplotlib
matplotlib.use('Agg')

import csv
import argparse as ap
import pandas 
from QSTK.qstkutil import DataAccess as da
import numpy as np
import math
import copy
import QSTK.qstkutil.qsdateutil as du
import datetime as dt
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep

"""
Accepts a list of symbols along with start and end date
Returns the Event Matrix which is a pandas Datamatrix
Event matrix has the following structure :
    |IBM |GOOG|XOM |MSFT| GS | JP |
(d1)|nan |nan | 1  |nan |nan | 1  |
(d2)|nan | 1  |nan |nan |nan |nan |
(d3)| 1  |nan | 1  |nan | 1  |nan |
(d4)|nan |  1 |nan | 1  |nan |nan |
...................................
...................................
Also, d1 = start date
nan = no information about any event.
1 = status bit(positively confirms the event occurence)
"""

# Get the data from the data store
storename = "Yahoo" # get data from our daily prices source
# Available field names: open, close, high, low, close, actual_close, volume
closefield = "actual_close"
volumefield = "volume"
window = 10

def findEvents(symbols, startday,endday, marketSymbol, args, verbose = False):

	# Reading the Data for the list of Symbols.	
	timeofday = dt.timedelta(hours = 16)
	timestamps = du.getNYSEdays(startday, endday, timeofday)
	dataobj = da.DataAccess('Yahoo')
	if verbose:
            print __name__ + " reading data"
	# Reading the Data
	close = dataobj.get_data(timestamps, symbols, closefield, verbose = verbose)
	
	# Completing the Data - Removing the NaN values from the Matrix
	close = (close.fillna(method='ffill')).fillna(method='backfill')

	
	# Calculating Daily Returns for the Market
#	tsu.returnize0(close.values)
	SPYValues = close[marketSymbol]

	mktneutDM = close
	np_eventmat = copy.deepcopy(mktneutDM)
	for sym in symbols:
		for time in timestamps:
			np_eventmat[sym][time]=np.NAN

	if verbose:
            print __name__ + " finding events"

	# Generating the Event Matrix
	# Event described is : Market falls more than 3% plus the stock falls 5% more than the Market
	# Suppose : The market fell 3%, then the stock should fall more than 8% to mark the event.
	# And if the market falls 5%, then the stock should fall more than 10% to mark the event.
	maxday = len(mktneutDM[marketSymbol])
	print mktneutDM.index[maxday -1 ]
	with open(args.outputfile, "w") as outfile:
		writer = csv.writer(outfile)

		for symbol in symbols:
			for i in range(2, len(mktneutDM[symbol])):
				if mktneutDM[symbol][i-1] >= args.price and mktneutDM[symbol][i] < args.price : # When stock fall below 5
					np_eventmat[symbol][i] = 1.0  #overwriting by the bit, marking the event
					mydate = mktneutDM.index[i]
					writer.writerow([mydate.year, mydate.month, mydate.day, symbol, 'Buy', 100])
					mydate = mktneutDM.index[maxday - 1] if i + args.day >= maxday else mktneutDM.index[i + args.day]
					writer.writerow([mydate.year, mydate.month, mydate.day, symbol, 'Sell', 100])

					if verbose:
						print symbol, mktneutDM.index[i], mktneutDM[symbol][i]
			
	return np_eventmat

def mkdate(datestring):
	return dt.datetime.strptime(datestring, '%Y-%m-%d')

#################################################
################ MAIN CODE ######################
#################################################

#
# Read program argument
# Example:
# python Backtester.py price 2008-01-01 2012-12-31 sp5002012 orders.csv
argparser = ap.ArgumentParser(description="Take price, holding day, start date, end date, symbol file and output order file.")
argparser.add_argument("price", type = float)
argparser.add_argument("day", type = int)
argparser.add_argument("datestart", type = mkdate)
argparser.add_argument("dateend", type = mkdate)
argparser.add_argument("symbolfile")
argparser.add_argument("outputfile")
argparser.add_argument('-v', '--verbose', action = 'count', default = 0, dest = 'verbose')
args = argparser.parse_args()
print type(args.datestart)
if args.verbose:
	print "Cutting price: " + str(args.price)
	print "Start date: " + str(args.datestart)
	print "End date: " + str(args.dateend)
	print "Symbol list file: " + args.symbolfile
	print "Output file: " + args.outputfile

dataobj = da.DataAccess('Yahoo')
symbols = dataobj.get_symbols_from_list(args.symbolfile)
symbols.append('SPY')
# You might get a message about some files being missing, don't worry about it.

startday = args.datestart
endday = args.dateend
findEvents(symbols, startday, endday, 'SPY', args, verbose = args.verbose)
