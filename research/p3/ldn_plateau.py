import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from orb import orb_entries, run, params, ctx
c = ctx(); tod = c['df'].tod.values
rows = []
for rs, re, we in itertools.product(('00:00', '01:00', '02:00', '03:00'), ('07:00', '07:30', '08:00', '08:30', '09:00', '09:30'), ('10:00', '10:30', '11:00', '11:30', '12:00')):
    for k in (0.08, 0.1, 0.12, 0.15, 0.2):
        E = orb_entries(rs, re, we, stop='kDR', k=k)
        for mg, P in (('eod', params(maxbars=1000)), ('R1@1 eod', params(maxbars=1000, tr_type=1, tr_dist=1.0, tr_act=1.0))):
            Tt = run(E, P)
            r = {'rs': rs, 're': re, 'we': we, 'k': k, 'mgmt': mg, 'n/day': len(Tt) / 730, 'exp': Tt.pnl.mean(), 'WR': (Tt.pnl > 1e-9).mean()}
            for y in (2023, 2024, 2025): r[y] = Tt[Tt.yr == y].pnl.mean()
            et = tod[Tt.e.values]; r['share_pre930'] = (et < 570).mean()
            r['exp_pre930'] = Tt[et < 570].pnl.mean(); r['exp_rth'] = Tt[et >= 570].pnl.mean()
            rows.append(r)
R = pd.DataFrame(rows); R['min_y'] = R[[2023, 2024, 2025]].min(axis=1)
R.to_pickle('../output/p3_ldn_plateau.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 300)
for mg in ('eod', 'R1@1 eod'):
    s = R[R.mgmt == mg]
    print(f'==== {mg}: share of {len(s)} configs with all years > 0: {(s.min_y > 0).mean():.2f}; median exp {s.exp.median():.3f}')
    print(s.groupby('rs')[['exp', 'min_y']].median().round(3).T.to_string())
    print(s.groupby('re')[['exp', 'min_y']].median().round(3).T.to_string())
    print(s.groupby('we')[['exp', 'min_y']].median().round(3).T.to_string())
    print(s.groupby('k')[['exp', 'min_y']].median().round(3).T.to_string())
b = R[(R.rs == '02:00') & (R.re == '08:00') & (R.we == '11:00')]
print(b.round(3).to_string(index=False))
