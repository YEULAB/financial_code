import pandas as pd
import numpy as np
from random import randint
from glob import glob
import os
import math
import operator

path = '/path/to/tickers/*.csv'
s = dict()
dataframes = dict()
for fpath in glob(path):
    ticker, _ = os.path.splitext(os.path.basename(fpath))
    #df = pd.DataFrame.from_csv(path, parse_dates=False)
    df = pd.read_table(fpath, sep=',')
    df.sort(columns=['Date'], inplace=True)
    df.index = df.index.order()
    df['Cumlative'] = df['Adj Close'] / df['Adj Close'][0]
    daily = df['Adj Close'][1:].values / df['Adj Close'][:-1].values - 1
    s[ticker] = math.sqrt(250) * np.average(daily) / np.std(daily)
    dataframes[ticker] = df

sharpes = list(reversed(sorted(s.iteritems(), key=operator.itemgetter(1))))