from lab import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf); L = daylevels(b)
pm = (b.tod >= 720) & (b.tod < 960)
c,o,h,l,atr,day = b.c,b.o,b.h,b.l,b.atr,b.day
n = len(c)
def break_retest(X, side, conf_atr, stop_atr, maxwait):
    """after a CLOSE beyond level X by >= conf_atr*ATR in PM, place limit at X (retest), stop beyond X by stop_atr*ATR.
       order lives for maxwait bars after breakout; one setup per level per day."""
    rows=[]
    done_day = -1
    i = 0
    brk = np.where(pm & ((c - X)*side >= conf_atr*atr))[0]
    last=-1
    for i in brk:
        if day[i]==last: continue
        # must be first close beyond X in PM today: previous PM closes not beyond
        last = day[i]
        e = X[i] + side*0.25
        rows.append(dict(sb=i, side=side, etype=2, eprice=e, sl=X[i] - side*stop_atr*atr[i], expiry=maxwait))
    return pd.DataFrame(rows)
for conf in [0.5, 1.0]:
    for stop in [0.5, 1.0]:
        allsig = []
        for name, X, side in [('amh',L['amh'],1),('aml',L['aml'],-1),('onh',L['onh'],1),('onl',L['onl'],-1),('pdh',L['pdh'],1),('pdl',L['pdl'],-1)]:
            s = break_retest(X, side, conf, stop, 30)
            s['lev']=name; allsig.append(s)
        sig = pd.concat(allsig)
        ladder(b, sig, ks=(1,1.5,2,3,4), label=f'H5 break-retest tf={tf} conf={conf}ATR stop={stop}ATR', max_per_day=3)
