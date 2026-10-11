import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from raw_events import sweep_raw, apply_rev
from events import run, summarize, ctx
def T(h, m): return h * 60 + m
c = ctx(); df = c['df']
R = sweep_raw(win_end=T(9, 30), N=60, min_depth=0.0, max_depth=99)
R['DR'] = df.DR.values[R.e.values]; R['rng_dr'] = R['size'] / R.DR; R['stod'] = df.tod.values[R.e.values - 1]
pd.set_option('display.width', 250, 'display.max_rows', 200)
cols = ['n/day', 'WR', 'exp', 'net', 'wo_top5%', 'Rpts', 2023, 2024, 2025, 'min_y']
def show(label, Rs, buf=0.3, tm='R', tv=2.0, **kw):
    s = summarize(run(apply_rev(Rs, buf, tm, tv), **kw)); print(f'{label:45s}', {k: round(float(s[k]), 3) for k in cols if k in s})
for buf in (0.3, 0.5):
    print(f'---- SL ext+{buf}*range, TP 2R')
    show('base', R, buf)
    for md in (0.05, 0.1, 0.15, 0.2): show(f'sweep depth >= {md} range', R[R.depth >= md], buf)
    for q in ((0, 0.15), (0.15, 0.25), (0.25, 0.4), (0.4, 9)): show(f'range/DR in {q}', R[(R.rng_dr >= q[0]) & (R.rng_dr < q[1])], buf)
    show('upper sweep -> SHORT', R[R.d < 0], buf); show('lower sweep -> LONG', R[R.d > 0], buf)
    show('signal 09:12-09:19', R[R.stod < T(9, 20)], buf); show('signal 09:20-09:29', R[R.stod >= T(9, 20)], buf)
    show('exit before cash open (flat 09:29)', R, buf, flat=T(9, 29))
    for mb in (15, 30, 60, 120): show(f'max hold {mb} min', R, buf, maxbars=mb)
