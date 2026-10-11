import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from rthbreak import rth_break_entries
from orb import run, params, ctx
c = ctx(); df = c['df']
pd.set_option('display.width', 250)
P_ = {'eod': params(maxbars=1000), 'chand20': params(maxbars=1000, tr_type=2, tr_dist=20), 'chand12': params(maxbars=1000, tr_type=2, tr_dist=12)}
for k in (0.08, 0.1, 0.12, 0.15):
    E = rth_break_entries('02:00', '08:00', '11:00', k=k, intact=True)
    for nm, P in P_.items():
        T = run(E, P).sort_values('e')
        x = T.pnl.values; srt = np.sort(x)[::-1]
        boot = [np.random.default_rng(i).choice(x, len(x)).mean() for i in range(2000)]
        print(f'k={k} {nm}: n={len(x)} exp={x.mean():.3f} median={np.median(x):.2f} | w/o top5 {srt[5:].mean():.3f} w/o top10 {srt[10:].mean():.3f} '
              f'| top5 share of total {srt[:5].sum()/x.sum():.2f} | boot 5%={np.percentile(boot,5):.3f} P(exp<=0)={np.mean(np.array(boot)<=0):.3f} '
              f'| long {T[T.d>0].pnl.mean():.3f} ({(T.d>0).sum()}) short {T[T.d<0].pnl.mean():.3f} ({(T.d<0).sum()})')
    # half-year stability
E = rth_break_entries('02:00', '08:00', '11:00', k=0.12, intact=True)
T = run(E, P_['chand20'])
h = T.groupby(pd.PeriodIndex(T.sess, freq='Q')).pnl.agg(['mean', 'sum', 'size']); print(h.round(2).T.to_string())
et = df.tod.values[T.e.values]; print('entry time distribution (ET):', pd.Series(et // 30 * 30).map(lambda t: f'{t//60:02d}:{t%60:02d}').value_counts().sort_index().to_dict())
print('exp by entry half-hour:', T.groupby(et // 30 * 30).pnl.mean().round(2).to_dict())
print('range size (DR units) quartiles -> exp:', T.groupby(pd.qcut(T.rng_dr, 4)).pnl.agg(['mean', 'size']).round(3).to_dict())
