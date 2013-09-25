import pandas as pd
import numpy as np
from random import randint
from glob import glob
import os
import math
import operator

orders_csv = 'data/orders.csv'
orders = pd.read_csv(orders_csv, parse_dates={'date':[0,1,2]}, skiprows=0, header=None)
orders = orders.sort(['date'])
orders['date'] = orders['date'] + timedelta(hours=16)

dt_start = orders['date'].min()
dt_I_WANT = dt_start
dt_end = orders['date'].max() + timedelta(days=1)
dt_timeofday = dt.timedelta(hours=16)
ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
c_dataobj = da.DataAccess('Yahoo')
ls_keys = ['close']
ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
d_data = dict(zip(ls_keys, ldf_data))

print d_data['close'][dt_I_WANT] 