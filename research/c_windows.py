"""Phase C: window scan (start x length) of continuation edge vs control.
Edge = P(+aR before -1R | trigger) - P(+aR before -1R | any bar, same window), same stop definition (1 ATR).
Day-clustered standard errors. IS = 2023-2024, OOS = 2025.
"""
import numpy as np, pandas as pd, sys
T = pd.read_pickle('output/B_events.pkl')
STOP = sys.argv[1] if len(sys.argv) > 1 else 'atr1'
T = T[T.stop == STOP]
T['sm'] = (T.etod - 18 * 60) % 1440          # entry minute since 18:00
ndays = T[T.trig == 'CTRL'].groupby('yr').sess.nunique()

def clustered(w, day):
    g = pd.DataFrame({'w': w, 'd': day}).groupby('d').w.agg(['sum', 'count'])
    p = g['sum'].sum() / g['count'].sum()
    se = np.sqrt(((g['sum'] - p * g['count']) ** 2).sum()) / g['count'].sum()
    return p, se

starts = range(0, 1380, 15); lens = (15, 30, 45, 60, 90, 120, 180, 240)
# precompute per (trig, sm-minute) sums to be fast
keys = ['win_0.25', 'win_0.5', 'win_1.0']
T['fe30'] = T.mfe30 - T.mae30
rows = []
groups = {k: g for k, g in T.groupby('trig')}
ctrl = groups['CTRL']
def stats(g, period):
    if period == 'IS': g = g[g.yr <= 2024]; nd = ndays[ndays.index <= 2024].sum()
    elif period == 'OOS': g = g[g.yr == 2025]; nd = ndays[2025]
    else: g = g[g.yr == period]; nd = ndays[period]
    return g, nd
out = []
for trig in ('IMP', 'BRK', 'PB'):
    G = groups[trig]
    for s in starts:
        for L in lens:
            if s + L > 1380: continue
            gm = G[(G.sm >= s) & (G.sm < s + L)]; cm = ctrl[(ctrl.sm >= s) & (ctrl.sm < s + L)]
            r = {'trig': trig, 'start': f'{(18*60+s)//60%24:02d}:{(18*60+s)%60:02d}', 'len': L}
            for per in ('IS', 'OOS', 2023, 2024, 2025):
                g, nd = stats(gm, per); cg, _ = stats(cm, per)
                r[f'n/d_{per}'] = len(g) / nd
                for k in keys:
                    p, se = clustered(g[k].values, g.sess.values) if len(g) > 30 else (np.nan, np.nan)
                    pc = cg[k].mean()
                    r[f'{k}_{per}'] = p; r[f'edge{k[3:]}_{per}'] = p - pc; r[f'z{k[3:]}_{per}'] = (p - pc) / se if se else np.nan
                r[f'fe30_{per}'] = g.fe30.mean() - cg.fe30.mean()
            out.append(r)
W = pd.DataFrame(out)
W.to_pickle(f'output/C_windows_{STOP}.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 300)
cols = ['trig', 'start', 'len', 'n/d_IS', 'win_0.5_IS', 'edge_0.5_IS', 'z_0.5_IS', 'edge_0.5_OOS', 'z_0.5_OOS',
        'edge_0.5_2023', 'edge_0.5_2024', 'edge_0.5_2025', 'edge_1.0_IS', 'edge_1.0_OOS', 'fe30_IS', 'fe30_OOS']
for trig in ('IMP', 'BRK', 'PB'):
    w = W[(W.trig == trig) & (W['n/d_IS'] >= 0.5)]
    print(f'==== {trig}: top 25 by IS z (edge +0.5R) ====')
    print(w.sort_values('z_0.5_IS', ascending=False)[cols].head(25).round(3).to_string(index=False))
