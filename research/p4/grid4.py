import numpy as np, pandas as pd, sys, os, itertools, time
sys.path.insert(0, os.path.dirname(__file__))
from raw_events import *
from events import run, summarize
def T(h, m): return h * 60 + m
rows = []; t0 = time.time()
# ---------------- reversal grid
for we, N, mind, maxd in itertools.product((T(9, 30), T(10, 0), T(10, 30), T(11, 30)), (1, 3, 5, 10, 20), (0.0, 0.1, 0.25), (0.5, 1.0, 2.0)):
    if mind >= maxd: continue
    R = sweep_raw(win_end=we, N=N, min_depth=mind, max_depth=maxd)
    for buf, (tm, tv) in itertools.product((0.05, 0.15, 0.3, 0.5), (('mid', 0), ('opp', 0), ('R', 1.0), ('R', 1.5), ('R', 2.0), ('R', 3.0))):
        for mb in (60, 1000):
            Tt = run(apply_rev(R, buf, tm, tv), maxbars=mb)
            rows.append({'fam': 'REV sweep-reclaim', 'we': we, 'N': N, 'mind': mind, 'maxd': maxd, 'sl': f'ext+{buf}', 'tp': f'{tm}{tv if tm == "R" else ""}', 'mb': mb, **summarize(Tt)})
print('rev done', round(time.time() - t0), flush=True)
# ---------------- continuation grid
for we, rt in itertools.product((T(9, 30), T(10, 0), T(10, 30), T(11, 30)), (False, True)):
    R = breakout_raw(win_end=we, retest=rt)
    for (sm, sv), (tm, tv) in itertools.product((('mid', 0), ('in', 0.25), ('in', 0.1), ('bar', 0.05), ('bar', 0.2)),
                                                (('R', 0.5), ('R', 1.0), ('R', 1.5), ('R', 2.0), ('R', 3.0), ('size', 0.5), ('size', 1.0))):
        for mb in (60, 1000):
            Tt = run(apply_brk(R, sm, sv, tm, tv), maxbars=mb)
            rows.append({'fam': 'CONT breakout' + (' retest' if rt else ''), 'we': we, 'N': np.nan, 'mind': np.nan, 'maxd': np.nan,
                         'sl': f'{sm}{sv if sm != "mid" else ""}', 'tp': f'{tm}{tv}', 'mb': mb, **summarize(Tt)})
print('cont done', round(time.time() - t0), flush=True)
G = pd.DataFrame(rows); G.to_pickle('../output/p4_grid.pkl')
pd.set_option('display.width', 260, 'display.max_rows', 200)
cols = ['fam', 'we', 'N', 'mind', 'maxd', 'sl', 'tp', 'mb', 'n/day', 'WR', 'avgW', 'avgL', 'exp', 'net', 'wo_top5%', 'Rpts', 2023, 2024, 2025, 'min_y']
for f in G.fam.unique():
    s = G[(G.fam == f) & (G['n/day'] >= 0.2)]
    print(f'===== {f}: {len(s)} configs | share all-years>0: {(s.min_y > 0).mean():.3f} | median exp {s.exp.median():.3f}')
    print(s.sort_values('IS', ascending=False)[cols].head(12).round(3).to_string(index=False))
