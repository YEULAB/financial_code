'''
@summary: Calculate Sharpe Ratio for all ticker 
'''
# Enable running in Ubuntu Server 12.10
import matplotlib
matplotlib.use('Agg')

import math
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import matplotlib.pyplot as plt
from pylab import *
import pandas

print pandas.__version__
#
# Prepare to read the data
startday = dt.datetime(2011, 1, 1)
endday = dt.datetime(2011, 12, 31)
timeofday=dt.timedelta(hours=16)
timestamps = du.getNYSEdays(startday, endday, timeofday)

#
#Read close data from symbols list
dataobj = da.DataAccess('Yahoo')
symbols = dataobj.get_all_symbols()
close = dataobj.get_data(timestamps, symbols, "close", verbose=True)

#
#Calculate daily_return
trading_date = close.index
daily_price = close.values.copy()
daily_rets = close.values.copy()
tsu.fillforward(daily_rets)
tsu.fillbackward(daily_rets)
tsu.returnize0(daily_rets)
sharpe_list = sorted(zip(tsu.get_sharpe_ratio(daily_rets), daily_price[-1, :] / daily_price[0, :] - 1, symbols), reverse=True)
#Filter NaN value
sharpe_list = [f for f in sharpe_list if not math.isnan(f[0]) and not math.isnan(f[1])]
print sharpe_list
