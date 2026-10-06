"""Anchored walk-forward of the whole selection process.
Configs: stop floor x management x compression params. For each test quarter (2024Q1..2025Q4) select the config with the best
expectancy on ALL data before that quarter (min 12 months), trade it in the quarter. Also report the fixed pre-registered candidate."""
import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
MG = {'t45': params(maxbars=45), 't60': params(maxbars=60), 't90': params(maxbars=90), 't120': params(maxbars=120),
      'p33@.5 t60': params(maxbars=60, pfrac=0.33, ptp=0.5), 'BE1.5+.5 t90': params(maxbars=90, be_trig=1.5, be_off=0.5),
      'aggrBE0.2': params(be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25)}
trades = {}
for floor, comp, look in itertools.product((1.5, 2.0, 2.5, 3.0), (2.0, 2.5, 3.0), (6, 8)):
    E = setup_entries('H3', stop_floor_atr=floor, comp=comp, look=look)
    for mg, P in MG.items():
        Tt = run(E, P, cost_pts=0.6); Tt['q'] = pd.PeriodIndex(Tt.sess, freq='Q')
        trades[(floor, comp, look, mg)] = Tt
quarters = pd.period_range('2024Q1', '2025Q4', freq='Q')
wf = []; picks = []
for q in quarters:
    best, bk = -9, None
    for k, Tt in trades.items():
        tr = Tt[Tt.q < q]
        if len(tr) < 100: continue
        v = tr.pnl.mean()
        if v > best: best, bk = v, k
    te = trades[bk][trades[bk].q == q]
    wf.append(te.assign(cfg=str(bk))); picks.append({'quarter': str(q), 'picked': bk, 'train_exp': best, 'test_exp': te.pnl.mean(), 'test_n': len(te)})
WF = pd.concat(wf)
pd.set_option('display.width', 250)
print(pd.DataFrame(picks).round(3).to_string(index=False))
m = metrics(WF, ndays=WF.sess.nunique() and 487)
print('WALK-FORWARD OOS 2024-2025:', {k: round(float(v), 3) for k, v in m.items()}, 'net exp', round(WF.pnl_net.mean(), 3))
fixed = trades[(2.0, 2.5, 6, 't60')]
for per, f in (('2024+2025 (WF period)', fixed.yr >= 2024), ('2025', fixed.yr == 2025)):
    print('FIXED candidate', per, {k: round(float(v), 3) for k, v in metrics(fixed[f]).items()})
# how many of the 168 configs are positive in 2025?
oos = pd.Series({k: v[v.yr == 2025].pnl.mean() for k, v in trades.items()})
print('configs positive in 2025:', (oos > 0).mean().round(3), 'median 2025 exp', oos.median().round(3))
print(oos.groupby(level=3).median().round(3))
WF.to_pickle('../output/p2_wf_trades.pkl')
