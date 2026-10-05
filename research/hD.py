from cand import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 3
b = B(tf); L = daylevels(b)
S = pd.Series; day=b.day; tod=b.tod; c,o,h,l,atr = b.c,b.o,b.h,b.l,b.atr
reg = np.nan_to_num(daily_regime(b, 50, 'ma'), nan=0)
amh, aml = L['amh'], L['aml']
ro = L['ro']
p12 = S(np.where(tod==720, c, np.nan)).groupby(day).transform('max').values
am_dir = np.sign(p12 - ro)
pm = (tod > 720) & (tod < 900)
ph = S(np.where(tod>720, h, -np.inf)).groupby(day).cummax().values
pl = S(np.where(tod>720, l, np.inf)).groupby(day).cummin().values
def rmax(x,n): return S(x).groupby(day).transform(lambda s: s.rolling(n, min_periods=1).max()).values
def rmin(x,n): return S(x).groupby(day).transform(lambda s: s.rolling(n, min_periods=1).min()).values
def summ(t):
    t = t[t.split!='OOS']; out=[]
    for sp in ['IS','VAL']:
        q = t[t.split==sp]; out.append(f'{sp}:{q.R.mean():+.3f}(n={len(q)},wr={(q.R>0).mean():.2f},risk={q.risk.mean():.0f})')
    return ' '.join(out)
amr = amh - aml
for use_reg in [False, True]:
  for rmin_, rmax_ in [(0.25,0.75),(0.38,0.8),(0.5,0.9)]:
    for N in [3, 5, 8]:
        rows=[]
        for side in (1,-1):
            ext = amh if side>0 else aml
            pb = pl if side>0 else ph            # pullback extreme in PM
            depth = ((ext - pb)/amr) if side>0 else ((pb - ext)/amr)
            trig_lvl = S(rmax(h, N) if side>0 else rmin(l, N)).groupby(day).shift(1).values   # prior N bars high
            cond = pm & (am_dir == side) & (depth >= rmin_) & (depth <= rmax_) & ((c - trig_lvl)*side > 0) & ((c - ext)*side < 0)
            if use_reg: cond &= (reg == side)
            idx = np.where(cond)[0]
            e = c[idx]
            sl = pb[idx] - side*0.25
            R = (e - sl)*side
            ok = (R > 0.5*atr[idx]) & (R < 4*atr[idx])
            idx, e, sl = idx[ok], e[ok], sl[ok]
            for tgt in ['ext']:
                tp = ext[idx]
            rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=0, eprice=e, sl=sl, tp=tp, expiry=1)))
        s = pd.concat(rows)
        t = b.run(s, max_per_day=1)
        s2 = s.copy(); s2['tp'] = s2.eprice + s2.side*2*(s2.eprice-s2.sl).abs()
        t2 = b.run(s2, max_per_day=1)
        s3 = s.drop(columns='tp')
        t3 = b.run(s3, max_per_day=1, trail_mode=1, trail_start_R=1.5, trail_param=1.0)
        print(f'reg={use_reg} depth[{rmin_},{rmax_}] N={N} | tgt=AMext {summ(t)} | 2R {summ(t2)} | trail {summ(t3)}')
