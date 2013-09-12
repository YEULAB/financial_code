import glob
from collections import Counter

#Check the number of data points in file
c = Counter()
for fname in glob.glob(os.path.join(path, '*.csv')):
    fpath = os.path.join(path, fname)
    with open(fpath) as f:
        c.update({len(f.readlines()): 1})

#Delete values with less than 253 data points
for fname in glob.glob(os.path.join(path, '*.csv')):
    fpath = os.path.join(path, fname)
    with open(fpath) as f:
        if len(f.readlines()) == 253:
            continue
    os.remove(fpath)
