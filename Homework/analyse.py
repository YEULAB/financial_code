# python imports
import cPickle
import sys
import numpy as np
# from pandas import DataMatrix
import datetime as dt
import random
import matplotlib.pyplot as plt
from pylab import *
import pandas
# qstk imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da

print sys.argv

workingSymbol = sys.argv[2]
fileName = sys.argv[1]
print "Analysing the market simulation tool with "+ fileName +" file, control "+ workingSymbol

symbols = np.loadtxt( fileName,delimiter=',',dtype='i4,i1,i,i',comments='#',skiprows=0)

startday = dt.date(symbols[0][0], symbols[0][1], symbols[0][2])
endday = dt.date(symbols[-1][0], symbols[-1][1], symbols[-1][2])
print "analysing data between", startday, "and", endday
timeofday=dt.timedelta(hours=16)
timestamps = du.getNYSEdays(startday,endday,timeofday)

dataobj = da.DataAccess('Yahoo')
# Reading the Data
close = dataobj.get_data(timestamps, [workingSymbol], "close")
pricedat=close.values
portfolioNormalised = map(lambda symbol : symbol[3]/float(symbols[0][3]), symbols)

plt.clf()
plt.cla()
plt.plot(timestamps, portfolioNormalised) 
plt.plot(timestamps, pricedat/pricedat[0])
plt.axhline(y=0,color='r')
plt.legend(['Portfolio', '$SPX'])
plt.ylabel('Daily Returns')
plt.xlabel('Date')
savefig('analyse.pdf',format='pdf')