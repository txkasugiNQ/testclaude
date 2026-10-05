from candB import *
b = B(2)
def summ(t):
    t = t[t.split!='OOS']
    g = t.groupby('split').R.agg(['mean','count']); w = t.groupby('split').R.apply(lambda r:(r>0).mean())
    return ' '.join(f'{sp}:{g.loc[sp,"mean"]:+.3f}(n={int(g.loc[sp,"count"])},wr={w.loc[sp]:.2f})' for sp in ['IS','VAL'])
for a in [-0.25, 0.0, 0.25, 0.5, 0.75]:
    for s_atr in [0.75, 1.0, 1.5]:
        for wait in [5, 15]:
            s = signals_B(b, a, s_atr, wait=wait)
            out=[]
            for k in [2, 3, 4]:
                s2 = s.copy(); s2['tp'] = s2.eprice + s2.side*k*(s2.eprice-s2.sl).abs()
                t = b.run(s2, max_per_day=2); out.append(f'R{k} '+summ(t))
            t = b.run(s, max_per_day=2, trail_mode=1, trail_start_R=2, trail_param=1.5); out.append('trail2/1.5 '+summ(t))
            print(f'a={a} stop={s_atr} wait={wait}: ' + ' || '.join(out))
