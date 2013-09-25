# python imports
import cPickle
import sys
import numpy as np
# from pandas import DataMatrix
import datetime as dt
import random

# qstk imports
import QSTK.qstkutil.qsdateutil as du

import QSTK.qstkutil.DataAccess as da


print "Running the market simulation tool with "+sys.argv[1] +" money, to "+sys.argv[2] 
symbols = np.loadtxt(sys.argv[2],delimiter=',',dtype='i4, i1, i, S4, S4, i',comments='#',skiprows=0)

startday = dt.date(symbols[0][0], symbols[0][1], symbols[0][2])
endday = dt.date(symbols[-1][0], symbols[-1][1], symbols[-1][2])

print "printing data between", startday, "and", endday
timeofday=dt.timedelta(hours=16)
timestamps = du.getNYSEdays(startday,endday,timeofday)

workingSymbols = set()
for i in range(0, symbols.shape[0]):
    workingSymbols.add(symbols[i][3])

# print "timestamps", timestamps

dataobj = da.DataAccess('Yahoo')
# Reading the Data
close = dataobj.get_data(timestamps, workingSymbols, "close")

cache=float(sys.argv[1])
portfolio={}
nextOrder = 0
output = open(sys.argv[3], "w")
for moment in timestamps:
    while nextOrder<symbols.shape[0] and moment.date() == dt.date(symbols[nextOrder][0], symbols[nextOrder][1], symbols[nextOrder][2]):
        symbol = symbols[nextOrder][3]
        amount = symbols[nextOrder][5]
        if symbols[nextOrder][4] == 'Sell':
            amount = -amount
        if symbol in portfolio:
            portfolio[symbol] = portfolio[symbol] + amount
        else:
            portfolio[symbol] = amount
        price = close[symbol][moment]
        cache = cache - price * amount
        print symbol, price, amount, price * amount, cache
        nextOrder = nextOrder + 1

    currValue=cache
    for symbol in portfolio.viewkeys():
        currValue = currValue + portfolio[symbol] * close[symbol][moment]
    print moment.date(), currValue, portfolio, nextOrder, "!!!", cache
    output.write('%(year)04d,%(month)02d,%(day)02d,%(value)d \n' % {"year":moment.year, "month":moment.month, "day":moment.day, "value":currValue })
    output.write(str(currValue) + "\n")

        
output.close
print "target: 1133860"
