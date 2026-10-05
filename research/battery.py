import sys, itertools, time
from levels import *
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf); L = more_levels(b)
c,o,h,l,atr,day,tod = b.c,b.o,b.h,b.l,b.atr,b.day,b.tod
S = pd.Series
lagf = lambda x,n: S(x).groupby(day).shift(n).values
pmwin = (tod >= 720 - tf) & (tod < 960)
names = ['amh','aml','onh','onl','pdh','pdl','ibh','ibl','luh','lul','p12','vw','vwu1','vwd1','vwu2','vwd2','poc','pdc','ro','mid','rh_prev','rl_prev']
L['rh_prev'] = lagf(L['rh'],1); L['rl_prev'] = lagf(L['rl'],1)
def events(X, ev, stopk):
    X = np.asarray(X, float)
    pX = lagf(X, 1)
    ok = pmwin & np.isfinite(X)
    sigs = []
    if ev == 'brk':      # stop order at level, from current side
        for side in (1, -1):
            cond = ok & ((X - c)*side > 0) & ((X - h)*side > 0 if side>0 else (l - X) > 0)
            idx = np.where(cond)[0]; e = X[idx] + side*0.25
            sigs.append(pd.DataFrame(dict(sb=idx, side=side, etype=1, eprice=e, sl=e - side*stopk*atr[idx], expiry=1)))
    elif ev == 'fade':   # limit at level against approach
        for side in (1, -1):   # side=+1: buy limit at X when price above
            cond = ok & ((c - X)*side > 0) & ((l - X) > 0 if side>0 else (h - X) < 0)
            idx = np.where(cond)[0]; e = X[idx]
            sigs.append(pd.DataFrame(dict(sb=idx, side=side, etype=2, eprice=e, sl=e - side*stopk*atr[idx], expiry=1)))
    elif ev == 'retest': # after a close-through by >=0.5ATR (prev close on other side within 5 bars), limit at X
        for side in (1, -1):
            crossed = ((c - X)*side >= 0.5*atr) & (pd.Series((lagf(c,1) - pX)*side < 0).groupby(day).transform(lambda s: s.rolling(5, min_periods=1).max()).values > 0)
            idx = np.where(ok & crossed)[0]; e = X[idx] + side*0.25
            sigs.append(pd.DataFrame(dict(sb=idx, side=side, etype=2, eprice=e, sl=e - side*stopk*atr[idx], expiry=10)))
    elif ev == 'reclaim':  # poke through and close back -> market next open, reverse direction
        for side in (1, -1):   # side +1: poked below X, closed above
            if side>0: cond = ok & (l < X) & (c > X) & (lagf(c,1) > pX)
            else: cond = ok & (h > X) & (c < X) & (lagf(c,1) < pX)
            idx = np.where(cond)[0]
            e = c[idx]
            if stopk == 0: sl = (l[idx]-0.25) if side>0 else (h[idx]+0.25)
            else: sl = e - side*stopk*atr[idx]
            sigs.append(pd.DataFrame(dict(sb=idx, side=side, etype=0, eprice=e, sl=sl, expiry=1)))
    elif ev == 'closebrk':  # close crosses level -> market next open in break direction
        for side in (1, -1):
            cond = ok & ((c - X)*side > 0) & ((lagf(c,1) - pX)*side < 0)
            idx = np.where(cond)[0]; e = c[idx]
            sl = X[idx] - side*stopk*atr[idx]
            sigs.append(pd.DataFrame(dict(sb=idx, side=side, etype=0, eprice=e, sl=sl, expiry=1)))
    s = pd.concat(sigs)
    s = s[((s.eprice - s.sl)*s.side) >= 3]
    return s
exits = [('R1',dict(k=1)),('R1.5',dict(k=1.5)),('R2',dict(k=2)),('R3',dict(k=3)),('trail',dict(trail_mode=1, trail_start_R=1.5, trail_param=1.0)),('hold',dict())]
windows = [(720,960),(720,840),(810,960),(840,960)]
rows=[]; t0=time.time()
for name in names:
    for ev in ['brk','fade','retest','reclaim','closebrk']:
        for stopk in ([0, 1.0] if ev=='reclaim' else [0.5, 1.0, 1.5]):
            sig = events(L[name], ev, stopk)
            if len(sig) < 50: continue
            for xn, xp in exits:
                s = sig.copy()
                kw = {k:v for k,v in xp.items() if k!='k'}
                if 'k' in xp: s['tp'] = s.eprice + s.side*xp['k']*(s.eprice - s.sl).abs()
                t = b.run(s, max_per_day=2, **kw)
                t = t[t.split!='OOS']
                for ws, we in windows:
                    tt = t[(t.etod - 1 >= ws) & (t.etod <= we)] if True else t
                    # NOTE: window applied post-hoc on fills (sequence effects ignored at screening stage)
                    r = dict(level=name, ev=ev, stop=stopk, exit=xn, win=f'{ws}-{we}')
                    for sp in ('IS','VAL'):
                        q = tt[tt.split==sp]
                        r[f'n_{sp}'] = len(q); r[f'exp_{sp}'] = q.R.mean() if len(q) else np.nan; r[f'wr_{sp}'] = (q.R>0).mean() if len(q) else np.nan
                        r[f'risk_{sp}'] = q.risk.mean() if len(q) else np.nan
                    rows.append(r)
    print(name, len(rows), f'{time.time()-t0:.0f}s', flush=True)
R = pd.DataFrame(rows); R.to_pickle(f'battery_tf{tf}.pkl')
