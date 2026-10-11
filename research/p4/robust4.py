import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from raw_events import sweep_raw, apply_rev
from events import run, summarize
def T(h, m): return h * 60 + m
rows = []
ranges = [(T(8, 12), T(9, 12)), (T(8, 0), T(9, 0)), (T(8, 5), T(9, 5)), (T(8, 10), T(9, 10)), (T(8, 15), T(9, 15)), (T(8, 20), T(9, 20)),
          (T(8, 30), T(9, 12)), (T(8, 0), T(9, 12)), (T(7, 30), T(9, 0)), (T(8, 12), T(9, 0)), (T(8, 30), T(9, 30))]
for (rs, re), we, N in itertools.product(ranges, (T(9, 25), T(9, 30), T(9, 31), T(9, 35), T(9, 45)), (5, 20, 60)):
    if we <= re: continue
    R = sweep_raw(rs=rs, re=re, win_end=we, N=N, min_depth=0.0, max_depth=99)
    for buf, (tm, tv) in itertools.product((0.2, 0.3, 0.5), (('R', 1.0), ('R', 2.0), ('R', 3.0), ('mid', 0), ('opp', 0))):
        Tt = run(apply_rev(R, buf, tm, tv), maxbars=1000)
        rows.append({'range': f'{rs//60:02d}:{rs%60:02d}-{re//60:02d}:{re%60:02d}', 'we': f'{we//60:02d}:{we%60:02d}', 'N': N, 'buf': buf,
                     'tp': f'{tm}{tv if tm == "R" else ""}', **summarize(Tt)})
G = pd.DataFrame(rows); G.to_pickle('../output/p4_robust.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 300)
print('overall share all-years>0:', (G.min_y > 0).mean().round(3))
print(G.groupby('range')[['exp', 'min_y', 'wo_top5%', 'n/day']].median().round(3).sort_values('exp', ascending=False).to_string())
print(G.groupby('we')[['exp', 'min_y', 'wo_top5%', 'n/day']].median().round(3).to_string())
print(G.groupby('N')[['exp', 'min_y', 'n/day']].median().round(3).to_string())
print(G.groupby(['buf', 'tp'])[['exp', 'min_y', 'wo_top5%', 'WR']].median().round(3).to_string())
b = G[(G.range == '08:12-09:12') & (G.we == '09:30')]
print(b.round(3).to_string(index=False))
