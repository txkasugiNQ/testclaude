from cand import *
b = B(2)
pd.set_option('display.width',250)
def summ(t):
    t = t[t.split!='OOS']
    g = t.groupby('split').R.agg(['mean','count'])
    gs = t.groupby(['split','side']).R.mean().unstack()
    return ' '.join(f'{sp}:{g.loc[sp,"mean"]:+.3f}(n={int(g.loc[sp,"count"])},L{gs.loc[sp,1]:+.2f},S{gs.loc[sp,-1]:+.2f})' for sp in ['IS','VAL'])
# windows
for win in [(720,780),(720,810),(720,840),(720,870),(720,900),(720,960),(780,900),(840,960)]:
    s = signals_A(b, 1.0, 50, 'ma', win)
    s['tp'] = s.eprice + s.side*3*(s.eprice-s.sl).abs()
    t = b.run(s, max_per_day=2)
    print('win', win, summ(t))
for w, kind in [(20,'ma'),(50,'ma'),(100,'ma'),(20,'ema'),(50,'ema'),(10,'ret'),(20,'ret'),(50,'ret')]:
    s = signals_A(b, 1.0, w, kind, (720,840)); s['tp'] = s.eprice + s.side*3*(s.eprice-s.sl).abs()
    t = b.run(s, max_per_day=2); print('regime', kind, w, summ(t))
