from cand import *
from path import path_stats
b = B(2); m = b.m
s = signals_A(b, 1.0, 50, 'ma', (720,840))
t = b.run(s, max_per_day=2)   # entries with 1ATR stop, hold to 16:00 -> gives entry points
t = t[t.split!='OOS'].copy()
atr_e = (t.eprice - t.sl).abs().values   # 1 ATR at signal
ks = np.array([0.5,1,1.5,2,3,4,5,6,8])
mae_b, t_r, mfe_t, mae_t, fin = path_stats(m.h, m.l, m.c, m.tod, m.day, t.eb.values.astype(np.int64), t.side.values.astype(np.int64),
                                           t.epx.values, atr_e, ks, 960)
print('N trades', len(t), 'mean ATR(pts)', atr_e.mean())
print('Unconstrained path (units = 1 ATR at signal) to 16:00:')
print(' MFE quantiles', np.quantile(mfe_t, [.1,.25,.5,.75,.9]).round(2), ' MAE quantiles', np.quantile(mae_t,[.1,.25,.5,.75,.9]).round(2))
for k_i, k in enumerate(ks):
    reached = ~np.isnan(mae_b[:,k_i])
    mb = mae_b[reached, k_i]
    print(f' reach +{k}ATR: {reached.mean():.3f}  | MAE before reaching: p50={np.median(mb):.2f} p75={np.quantile(mb,.75):.2f} p90={np.quantile(mb,.9):.2f}  | median mins={np.median(t_r[reached,k_i]):.0f}')
# P(reach +k before -s) for stops s
print('\nP(reach +k ATR before -s ATR):')
for sstop in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
    row = []
    for k_i, k in enumerate(ks):
        win = (~np.isnan(mae_b[:,k_i])) & (mae_b[:,k_i] < sstop)
        row.append(win.mean())
    # expectancy for fixed target k in R units (k/sstop R) ignoring time exits
    print(f' stop {sstop}: ' + ' '.join(f'+{k}:{p:.2f}' for k,p in zip(ks,row)) + '  | E[R] fixed tgt: ' + ' '.join(f'{(p*k/sstop - (1-p)):+.2f}' for k,p in zip(ks,row)))
