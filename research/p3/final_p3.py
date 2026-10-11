import numpy as np, pandas as pd, sys, os, itertools, json
sys.path.insert(0, os.path.dirname(__file__))
from rthbreak import rth_break_entries
from orb import run, params, ctx
from fragility import frag
from mgmt_ldn import MGS
c = ctx(); df = c['df']
ALLD = pd.Series(df.sess[df.good].unique())
CANDS = {'A: LDN intact, k0.12, Chandelier 20xATR1m': (0.12, params(maxbars=1000, tr_type=2, tr_dist=20)),
         'B: LDN intact, k0.15, TP 5R': (0.15, params(maxbars=1000, tp=5)),
         'C: LDN intact, k0.15, 50% @+1R, Rest Trail 1R ab +2R': (0.15, params(maxbars=1000, pfrac=0.5, ptp=1.0, tr_type=1, tr_dist=1.0, tr_act=2.0))}
out = {}
for nm, (k, P) in CANDS.items():
    T = run(rth_break_entries('02:00', '08:00', '11:00', k=k, intact=True), P)
    x = T.pnl.values; eq = np.cumsum(x)
    days = len(ALLD); w = x > 1e-9; l = x < -1e-9
    s = 0; ms = 0
    for v in x: s = s + 1 if v < -1e-9 else 0; ms = max(ms, s)
    r = {'trades': len(x), 'tr/day': len(x) / days, 'tr/month': len(x) / days * 21, '% days with trade': len(x) / days,
         'WR': w.mean(), 'avgW': x[w].mean(), 'avgL': x[l].mean(), 'exp': x.mean(), 'exp_net': T.pnl_net.mean(), 'PF': x[w].sum() / -x[l].sum(),
         'maxDD': (np.maximum.accumulate(eq) - eq).max(), 'maxLstreak': ms, **frag(x), 'Rpts_med': T.Rpts.median(), 'dur_med_min': T.bars.median(),
         'long': T[T.d > 0].pnl.mean(), 'short': T[T.d < 0].pnl.mean(), 'MFE_med': T.mfe.median(), 'MAE_med': T.mae.median()}
    for y in (2023, 2024, 2025): r[f'y{y}'] = T[T.yr == y].pnl.mean()
    q = T.groupby(pd.PeriodIndex(T.sess, freq='Q')).pnl.sum(); r['pos_quarters'] = (q > 0).mean()
    out[nm] = r
    T.to_pickle(f'../output/p3_cand_{nm[0]}.pkl')
F = pd.DataFrame(out); pd.set_option('display.width', 250, 'display.max_rows', 100)
print(F.round(3).to_string())
# walk-forward of the selection over k x management (quarterly, anchored, >=4 quarters history)
trades = {}
for k in (0.08, 0.1, 0.12, 0.15, 0.2):
    E = rth_break_entries('02:00', '08:00', '11:00', k=k, intact=True)
    for mg, P in MGS().items():
        T = run(E, P); T['q'] = pd.PeriodIndex(T.sess, freq='Q'); trades[(k, mg)] = T
for crit in ('exp', 'robust'):
    wf = []; picks = []
    for q in pd.period_range('2024Q1', '2025Q4', freq='Q'):
        def score(t):
            tr = t[t.q < q].pnl.values
            if crit == 'exp': return tr.mean()
            return np.sort(tr)[::-1][max(1, int(0.05 * len(tr))):].mean()    # expectancy without top 5% (user's rule)
        bk = max(trades, key=lambda kk: score(trades[kk]))
        te = trades[bk][trades[bk].q == q]; wf.append(te); picks.append((str(q), bk, round(te.pnl.mean(), 3)))
    W = pd.concat(wf)
    print(f'WF ({crit}):', picks); print('   WF OOS exp', round(W.pnl.mean(), 3), 'n', len(W), 'WR', round((W.pnl > 0).mean(), 3), frag(W.pnl.values))
