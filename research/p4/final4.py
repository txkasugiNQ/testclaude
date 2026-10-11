import numpy as np, pandas as pd, sys, os, itertools, json
sys.path.insert(0, os.path.dirname(__file__))
from raw_events import sweep_raw, apply_rev
from events import run, summarize, ctx
def T(h, m): return h * 60 + m
c = ctx(); df = c['df']; ALLD = pd.Series(df.sess[df.good].unique())
R = sweep_raw(win_end=T(9, 30), N=60, min_depth=0.0, max_depth=99)
R['rng_dr'] = R['size'] / df.DR.values[R.e.values]
pd.set_option('display.width', 250, 'display.max_rows', 200)
# ---------- walk-forward of the selection process
trades = {}
for mr, buf, tv in itertools.product((0.0, 0.1, 0.15, 0.2, 0.25), (0.3, 0.4, 0.5), (1.5, 2.0, 2.5, 3.0)):
    t = run(apply_rev(R[R.rng_dr >= mr], buf, 'R', tv)); t['q'] = pd.PeriodIndex(t.sess, freq='Q'); trades[(mr, buf, tv)] = t
for crit in ('exp', 'tstat'):
    wf, picks = [], []
    for q in pd.period_range('2024Q1', '2025Q4', freq='Q'):
        def sc(t):
            x = t[t.q < q].pnl.values
            return x.mean() if crit == 'exp' else x.mean() / (x.std() / np.sqrt(len(x)))
        bk = max(trades, key=lambda k: sc(trades[k])); te = trades[bk][trades[bk].q == q]; wf.append(te); picks.append((str(q), bk, round(te.pnl.mean(), 2), len(te)))
    W = pd.concat(wf); print(f'WF[{crit}]', picks); print('   OOS:', {k: round(float(v), 3) for k, v in summarize(W, ndays=int(ALLD.dt.year.isin([2024, 2025]).sum())).items() if k in ('n/day', 'WR', 'exp', 'net', 'wo_top5%', 'PF')})
# ---------- final candidates (plateau centre) + unfiltered variant
FINAL = {'V2 (range>=0.20 DR, SL ext+0.4R, TP 2R)': (0.20, 0.4, 2.0), 'V1 (no size filter, SL ext+0.4R, TP 2R)': (0.0, 0.4, 2.0)}
out = {}
for nm, (mr, buf, tv) in FINAL.items():
    t = run(apply_rev(R[R.rng_dr >= mr], buf, 'R', tv)).sort_values('e')
    x = t.pnl.values; eq = np.cumsum(x); s = 0; ms = 0
    for v in x: s = s + 1 if v < 0 else 0; ms = max(ms, s)
    D = t.groupby('sess').pnl.sum().reindex(ALLD.values).fillna(0); nt = t.groupby('sess').size().reindex(ALLD.values).fillna(0)
    q = t.groupby(pd.PeriodIndex(t.sess, freq='Q')).pnl.sum()
    r = {**summarize(t), 'trades': len(t), 'tr/week': len(t) / len(ALLD) * 5, 'tr/month': len(t) / len(ALLD) * 21, 'maxDD': (np.maximum.accumulate(eq) - eq).max(),
         'maxLstreak': ms, 'long': t[t.d > 0].pnl.mean(), 'short': t[t.d < 0].pnl.mean(), 'n_long': int((t.d > 0).sum()), 'n_short': int((t.d < 0).sum()),
         'dur_med_min': t.bars.median(), 'dur_mean_min': t.bars.mean(), 'MAE_med': t.mae.median(), 'TP%': (t.reason == 2).mean(), 'SL%': (t.reason == 1).mean(), 'time%': (t.reason == 3).mean(),
         'pos_quarters': (q > 0).mean(), 'days_0': (nt == 0).mean(), 'days_1': (nt == 1).mean(), 'days_2+': (nt >= 2).mean(),
         'pos_days_of_traded': (D[nt > 0] > 0).mean(), '+1R_days': (D >= 1).mean(), '-1R_days': (D <= -1).mean(), 'avg_daily_R': D.mean(),
         'max_daily_loss': D.min()}
    for cpt in (0.0, 1.0, 2.0): r[f'exp_cost{cpt}'] = (t.pnl - cpt / t.Rpts).mean()
    out[nm] = r; t.to_pickle(f'../output/p4_final_{nm[:2]}.pkl')
F = pd.DataFrame(out); print(F.round(3).to_string()); F.to_csv('../output/p4_final_metrics.csv')
