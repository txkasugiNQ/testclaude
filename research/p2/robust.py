"""Plateau / robustness around H3 candidates. Selection metric = IS (2023-24) expectancy; 2025 shown but NOT used."""
import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
from candidates import T
MG = {'time60': params(maxbars=60), 'time90': params(maxbars=90), 'time120': params(maxbars=120), 'time45': params(maxbars=45),
      'swing10@1': params(tr_type=4, tr_act=1.0, tr_dist=10, maxbars=120), 'part50@1+BE': params(pfrac=0.5, ptp=1.0, be_trig=1.0, maxbars=90),
      'aggrBE0.2': params(be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25)}
rows = []
base_kw = dict(comp=2.5, look=6, brk_k=1.0, dmin=0.5, retr_max=0.6, stop_floor_atr=2.0, win=(T(12, 0), T(14, 30)), arm_to=T(14, 15))
variants = [('base', {})]
for v in (2.0, 3.0): variants.append((f'comp{v}', {'comp': v}))
for v in (4, 8): variants.append((f'look{v}', {'look': v}))
for v in (0.8, 1.2): variants.append((f'brk{v}', {'brk_k': v}))
for v in (0.3, 0.8): variants.append((f'dmin{v}', {'dmin': v}))
for v in (0.4, 0.8): variants.append((f'retr{v}', {'retr_max': v}))
for v in (1.5, 2.5, 3.0): variants.append((f'floor{v}', {'stop_floor_atr': v}))
for a, b in ((T(11, 45), T(14, 15)), (T(12, 15), T(14, 45)), (T(11, 30), T(14, 30)), (T(12, 0), T(14, 0)), (T(12, 30), T(15, 0)), (T(11, 0), T(14, 30))):
    variants.append((f'win{a//60}:{a%60:02d}-{b//60}:{b%60:02d}', {'win': (a, b), 'arm_to': b - 15}))
for name, kw in variants:
    E = setup_entries('H3', **{**base_kw, **kw})
    for mg, P in MG.items():
        Tt = run(E, P, cost_pts=0.6)
        r = {'variant': name, 'mgmt': mg, 'tr/day': len(Tt) / 730}
        for per, f in (('IS', Tt.yr <= 2024), ('2023', Tt.yr == 2023), ('2024', Tt.yr == 2024), ('OOS25', Tt.yr == 2025)):
            r[per] = Tt[f].pnl.mean()
        r['IS_net'] = Tt[Tt.yr <= 2024].pnl_net.mean()
        r['WR_IS'] = (Tt[Tt.yr <= 2024].pnl > 1e-9).mean()
        rows.append(r)
R = pd.DataFrame(rows); R.to_csv('../output/p2_robust.csv', index=False)
pd.set_option('display.width', 250, 'display.max_rows', 400)
for mg in MG:
    print(f'--- {mg}'); print(R[R.mgmt == mg].drop(columns='mgmt').round(3).to_string(index=False))
