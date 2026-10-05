from lab import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf); L = daylevels(b)
pm = (b.tod >= 720) & (b.tod < 960)
vw = b.vw
def lowest(x, n): return pd.Series(x).rolling(n, min_periods=1).min().values
def highest(x, n): return pd.Series(x).rolling(n, min_periods=1).max().values
for stopdef in ['fix10','fix20','atr2','swing10']:
    for vwf in [False]:
        rows = []
        # long: break of AMH
        condL = pm & (b.c < L['amh']) & (b.h < L['amh'])  # not yet above at this bar
        condS = pm & (b.c > L['aml']) & (b.l > L['aml'])
        if vwf:
            condL &= b.c > vw; condS &= b.c < vw
        for side, cond, lev in [(1, condL, L['amh']+0.25), (-1, condS, L['aml']-0.25)]:
            idx = np.where(cond)[0]
            e = lev[idx]
            if stopdef=='fix10': sl = e - side*10
            elif stopdef=='fix20': sl = e - side*20
            elif stopdef=='atr2': sl = e - side*2*b.atr[idx]
            else:
                sl = (lowest(b.l, 10)[idx]-0.25) if side>0 else (highest(b.h,10)[idx]+0.25)
            rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=1, eprice=e, sl=sl, expiry=1)))
        sig = pd.concat(rows)
        sig = sig[(sig.eprice-sig.sl)*sig.side > 2]
        ladder(b, sig, label=f'H1 AM-extreme breakout tf={tf} stop={stopdef} vwapfilter={vwf}', max_per_day=1)
