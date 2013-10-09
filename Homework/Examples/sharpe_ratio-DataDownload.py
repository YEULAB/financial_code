import requests
import os


tickers_file = '/Users/seanokeefe/Desktop/Github/financial_code/work/data/file.txt'
with open(tickers_file) as f:
    tickers = [l.strip() for l in f.readlines()]

# path is where I save downloaded tickers
path = '/Users/seanokeefe/Desktop/Github/financial_code/work/data/'
# Yahoo API URL
url = "http://ichart.finance.yahoo.com/table.csv"
# Yahoo get parameters where date range 2011/01/01 - 2012/01/01
# although 2012/01/01 is an international holiday and won't be in the data
get_params = "s=%(t)s&a=00&b=01&c=2011&d=00&e=01&f=2012&g=d&ignore=.csv"
url = '?'.join([url, get_params])
for t in tickers:
    r = requests.get(url % {'t': t})
    if r.status_code != 200:
        continue
    fname = os.path.join(path, '%(t)s.csv' % {'t': t})
    with open(fname, 'w') as f:
        f.write(r.text)