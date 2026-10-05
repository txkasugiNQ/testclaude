from lab import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf)
c,o,h,l,atr,day,tod = b.c,b.o,b.h,b.l,b.atr,b.day,b.tod
S = pd.Series
def rmax(x,n): return S(x).groupby(day).transform(lambda s: s.rolling(n, min_periods=n).max()).values
def rmin(x,n): return S(x).groupby(day).transform(lambda s: s.rolling(n, min_periods=n).min()).values
lagf = lambda x,n: S(x).groupby(day).shift(n).values
pm = (tod >= 720) & (tod < 950)
res = []
for F in [8, 12]:            # flag length (bars)
  for IMP in [15]:           # impulse window before flag (bars)
    for imp_k in [3.0, 4.0]: # impulse size in ATR
      for flag_k in [1.5, 2.0]:  # flag max range in ATR
        fh = rmax(h, F); fl = rmin(l, F)            # flag range over last F bars (incl current)
        # impulse: move over IMP bars ending at flag start
        c_start = lagf(c, F + IMP); c_fs = lagf(c, F)
        atr_f = lagf(atr, F)
        imp = (c_fs - c_start)/atr_f
        flag_rng = (fh - fl)/atr_f
        rows=[]
        for side in (1,-1):
            cond = pm & (imp*side >= imp_k) & (flag_rng <= flag_k)
            # flag must hold upper half of impulse
            if side>0: cond &= fl > (c_start + c_fs)/2
            else: cond &= fh < (c_start + c_fs)/2
            idx = np.where(cond)[0]
            e = (fh[idx] + 0.25) if side>0 else (fl[idx] - 0.25)
            sl = (fl[idx] - 0.25) if side>0 else (fh[idx] + 0.25)
            rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=1, eprice=e, sl=sl, expiry=1)))
        sig = pd.concat(rows)
        lab_ = f'H6 flag tf={tf} F={F} IMP={IMP} impk={imp_k} flagk={flag_k}'
        ladder(b, sig, ks=(1,2,3), label=lab_, max_per_day=2)
        s2 = sig.copy()
        t = b.run(s2, trail_mode=1, trail_start_R=1.5, trail_param=1, max_per_day=2); report(t, b, '  trail1.5/1')
        t = b.run(s2, max_per_day=2); report(t, b, '  hold')
