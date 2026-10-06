import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
from candidates import T
rows = []
cfgs = {'H1 MID 15m-IMP': dict(name='H1', win=(T(12, 0), T(14, 30)), arm_to=T(14, 15)),
        'H2 AM 5m cluster': dict(name='H2', win=(T(9, 45), T(12, 15)), arm_to=T(12, 0)),
        'H2c MID 5m cluster': dict(name='H2', win=(T(12, 0), T(14, 30)), arm_to=T(14, 15)),
        'H1c AM 15m-IMP': dict(name='H1', win=(T(9, 45), T(12, 15)), arm_to=T(12, 0)),
        'H3 MID (candidate)': dict(name='H3')}
for nm, kw in cfgs.items():
    for mode in ('pb', 'imm'):
        if nm.startswith('H3') and mode == 'imm': continue
        for floor in (2.0, 3.0):
            E = setup_entries(stop_floor_atr=floor, mode=mode, **kw)
            for mg, P in (('t60', params(maxbars=60)), ('t90', params(maxbars=90))):
                Tt = run(E, P, cost_pts=0.6)
                r = {'setup': nm, 'entry': mode, 'floor': floor, 'mgmt': mg, 'tr/day': len(Tt) / 730}
                for y in (2023, 2024, 2025): r[y] = Tt[Tt.yr == y].pnl.mean()
                r['all'] = Tt.pnl.mean(); rows.append(r)
pd.set_option('display.width', 250)
print(pd.DataFrame(rows).round(3).to_string(index=False))
