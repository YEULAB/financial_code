# QSTK Imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
# Third Party Imports
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import itertools
a1 = 0.0
b1 = 0.0
c1 = 0.0
d1 = 0.0
allocation_increments = np.arange(0.0, 1.01, 0.1)
for a1 in allocation_increments:
    for b1 in allocation_increments:
        for c1 in allocation_increments:
            for d1 in allocation_increments:
                if (a1+b1+c1+d1) == 1.0:
                    print "Allocation", a1, b1, c1, d1
                    dt_start = dt.datetime(2011, 1, 1)
                    dt_end = dt.datetime(2011, 12, 31)
                    ls_symbols = ["C", "GS", "IBM", "HNZ"]
                    ls_alloc = [a1,b1,c1,d1]
                    # We need closing prices so the timestamp should be hours=16.
                    dt_timeofday = dt.timedelta(hours=16)
                    # Get a list of trading days between the start and the end.
                    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
                    # Creating an object of the dataaccess class with Yahoo as the source.
                    c_dataobj = da.DataAccess('Yahoo')
                    # Keys to be read from the data, it is good to read everything in one go.
                    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
                    
                    # Reading the data, now d_data is a dictionary with the keys above.
                    # Timestamps and symbols are the ones that were specified before.
                    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
                    d_data = dict(zip(ls_keys, ldf_data))
                    # Getting the numpy ndarray of close prices.
                    na_price = d_data['close'].values
                    # Normalizing the prices to start at 1 and see relative returns
                    na_normalized_price = na_price / na_price[0, :]
                    #Multiply each column by the allocation to the corresponding equity.
                    na_normalized = na_normalized_price.copy()
                    na_price_alloc = na_normalized * ls_alloc
                    
                    #Sum each row for each day. That's your cumulative daily portfolio value.
                    na_portfolio = np.sum(na_price_alloc, axis=1)
                    na_port = na_portfolio.copy()
                    
                    # Copy the normalized prices to a new ndarry to find returns.
                    na_ret = tsu.returnize0(na_port)
                    #Statistics from the total portfolio value.
                    daily_return = np.average(na_ret)
                    vol = np.std(na_ret)
                    sharpe_ratio = ((252)**(.5))*(daily_return/vol)
                    cum_ret = na_portfolio[len(na_portfolio)-1]
                    print "Share Ratio", sharpe_ratio
                    print "Volume", vol
                    print "Daily Return", daily_return
                    print "Culumitive Return", cum_ret

