from lab import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf); L = daylevels(b)
pm = (b.tod >= 720) & (b.tod < 960)
c,o,h,l,atr = b.c,b.o,b.h,b.l,b.atr
S = pd.Series
lagf = lambda x,n: S(x).groupby(b.day).shift(n).values
# levels as known BEFORE this bar (use previous bar's running values for rth hi/lo)
levels = {'amh':(L['amh'],-1),'aml':(L['aml'],1),'onh':(L['onh'],-1),'onl':(L['onl'],1),
          'pdh':(L['pdh'],-1),'pdl':(L['pdl'],1),'rth_hi':(lagf(L['rh'],1),-1),'rth_lo':(lagf(L['rl'],1),1)}
allsig=[]
for name,(X,side) in levels.items():
    # bearish sweep (side=-1): high > X and close < X, and previous close below X (first poke)
    if side<0:
        cond = pm & (h > X) & (c < X) & (lagf(c,1) < X)
        sl = h + 0.25
    else:
        cond = pm & (l < X) & (c > X) & (lagf(c,1) > X)
        sl = l - 0.25
    idx = np.where(cond)[0]
    e = c[idx]
    sig = pd.DataFrame(dict(sb=idx, side=side, etype=0, eprice=e, sl=sl[idx], expiry=1, lev=name))
    sig = sig[(sig.eprice - sig.sl).abs() >= 4]   # ignore microscopic stops
    allsig.append(sig)
    ladder(b, sig, ks=(0.5,1,1.5,2,3), label=f'H4 sweep-reclaim {name} tf={tf} market@next open, stop beyond sweep', max_per_day=3)
sig = pd.concat(allsig)
ladder(b, sig, ks=(0.5,1,1.5,2,3), label=f'H4 ALL levels tf={tf}', max_per_day=3)
