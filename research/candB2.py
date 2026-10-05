from candB import *
b = B(2)
def summ(t):
    t = t[t.split!='OOS']
    g = t.groupby('split').R.agg(['mean','count']); w = t.groupby('split').R.apply(lambda r:(r>0).mean())
    return ' '.join(f'{sp}:{g.loc[sp,"mean"]:+.3f}(n={int(g.loc[sp,"count"])},wr={w.loc[sp]:.2f})' for sp in ['IS','VAL'])
base = dict(a=0.5, s_atr=0.75, wait=15)
s = signals_B(b, **base); s['tp'] = s.eprice + s.side*3*(s.eprice-s.sl).abs()
t = b.run(s, max_per_day=2); print('BASE a=.5 s=.75 w=15 R3:', summ(t))
print(quarters(t).round(2).T)
print('by side', t[t.split!='OOS'].groupby(['split','side']).R.agg(['mean','count']).round(3).to_dict())
# no trend filter: both sides always (regime replaced by side itself)
import cand
orig = cand.daily_regime
for kind_desc, fn in [('NO FILTER long-only', lambda b,w,k: np.ones(len(b.c))), ('NO FILTER short-only', lambda b,w,k: -np.ones(len(b.c))),
                      ('COUNTER-trend', lambda b,w,k: -orig(b,w,k))]:
    import candB as cb
    cb.daily_regime = fn
    s = signals_B(b, **base); s['tp'] = s.eprice + s.side*3*(s.eprice-s.sl).abs()
    t = b.run(s, max_per_day=2); print(kind_desc, summ(t))
cb.daily_regime = orig
