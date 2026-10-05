from lab import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf); L = daylevels(b)
pm = (b.tod >= 720) & (b.tod < 960)
for off in [0, 5, 10]:
  for stop in [10, 15, 25]:
    rows=[]
    for side, lev, cond in [(-1, L['amh'], pm & (b.h < L['amh'])), (1, L['aml'], pm & (b.l > L['aml']))]:
        idx = np.where(cond)[0]
        e = lev[idx] - side*off   # short: sell limit above AMH by off
        rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=2, eprice=e, sl=e - side*stop, expiry=1)))
    sig = pd.concat(rows)
    ladder(b, sig, ks=(0.5,1,1.5,2,3), label=f'H3 fade AM extreme limit tf={tf} off={off} stop={stop}', max_per_day=2)
