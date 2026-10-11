import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from raw_events import sweep_raw, apply_rev
from events import run, summarize, ctx
def T(h, m): return h * 60 + m
c = ctx(); df = c['df']
rows = []
for (rs, re) in ((T(8, 12), T(9, 12)), (T(8, 0), T(9, 12)), (T(8, 10), T(9, 10)), (T(8, 15), T(9, 15)), (T(8, 5), T(9, 5))):
    for we in (T(9, 25), T(9, 30)):
        R = sweep_raw(rs=rs, re=re, win_end=we, N=60, min_depth=0.0, max_depth=99)
        R['rng_dr'] = R['size'] / df.DR.values[R.e.values]
        for mr, buf, tv in itertools.product((0.0, 0.1, 0.15, 0.2, 0.25), (0.3, 0.4, 0.5), (1.5, 2.0, 2.5, 3.0)):
            s = summarize(run(apply_rev(R[R.rng_dr >= mr], buf, 'R', tv)))
            rows.append({'range': f'{rs//60:02d}:{rs%60:02d}-{re//60:02d}:{re%60:02d}', 'we': we, 'min_rng': mr, 'buf': buf, 'tp': tv, **s})
G = pd.DataFrame(rows); G.to_pickle('../output/p4_sizefilter.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 200)
print(G.groupby('min_rng')[['exp', 'min_y', 'wo_top5%', 'n/day', 'OOS']].median().round(3).to_string())
print(G.groupby('min_rng').apply(lambda s: (s.min_y > 0).mean(), include_groups=False).round(3).rename('share_all_years_pos').to_string())
print(G.groupby(['range', 'min_rng'])['exp'].median().unstack().round(3).to_string())
b = G[(G.range == '08:12-09:12') & (G.we == T(9, 30)) & (G.min_rng.isin([0.0, 0.15, 0.2]))]
print(b[['min_rng', 'buf', 'tp', 'n/day', 'WR', 'exp', 'net', 'wo_top5%', 'Rpts', 2023, 2024, 2025, 'min_y']].round(3).to_string(index=False))
