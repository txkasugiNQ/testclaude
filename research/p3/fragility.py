"""Fragility metric (user's hard rule): does the strategy survive without its biggest winners?
 exp_wo_top5pct = expectancy after removing the best 5% of trades; top5_share = sum of 5 best trades / total R."""
import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from rthbreak import rth_break_entries
from orb import run, params
from mgmt_ldn import MGS
def frag(x):
    x = np.sort(np.asarray(x))[::-1]; n = len(x); k = max(1, int(round(0.05 * n)))
    return {'exp': x.mean(), 'exp_wo_top5pct': x[k:].mean(), 'top5_share': x[:5].sum() / x.sum() if x.sum() > 0 else np.nan}
def fragility_table(E_by_k, label):
    rows = []
    for k, E in E_by_k.items():
        for mg, P in MGS().items():
            T = run(E, P)
            r = {'set': label, 'k': k, 'mgmt': mg, 'n/day': len(T) / 730, 'WR': (T.pnl > 1e-9).mean(), **frag(T.pnl.values),
                 'IS': T[T.yr <= 2024].pnl.mean(), 'OOS': T[T.yr == 2025].pnl.mean(), 'avgW': T.pnl[T.pnl > 1e-9].mean(), 'avgL': T.pnl[T.pnl < -1e-9].mean()}
            for y in (2023, 2024): r[y] = T[T.yr == y].pnl.mean()
            q = T.groupby(pd.PeriodIndex(T.sess, freq='Q')).pnl.sum(); r['pos_quarters'] = (q > 0).mean()
            rows.append(r)
    return pd.DataFrame(rows)
if __name__ == '__main__':
    tabs = []
    for intact in (True, False):
        Es = {k: rth_break_entries('02:00', '08:00', '11:00', k=k, intact=intact) for k in (0.1, 0.15, 0.2, 0.25)}
        tabs.append(fragility_table(Es, 'LDN intact' if intact else 'LDN any'))
    R = pd.concat(tabs); R['min_y'] = R[[2023, 2024, 'OOS']].min(axis=1)
    R.to_pickle('../output/p3_fragility.pkl')
    pd.set_option('display.width', 260, 'display.max_rows', 200)
    ok = R[(R.exp_wo_top5pct > 0.05) & (R.min_y > 0) & (R.top5_share < 0.5)]
    print('configs passing [exp w/o top5% > 0.05, all years > 0, top5 share < 50%]:', len(ok), 'of', len(R))
    print(ok.sort_values('exp_wo_top5pct', ascending=False).head(30).round(3).to_string(index=False))
