"""Final candidate system: 'Day-Trend Pullback Continuation' (two windows, three arm types, one entry machine)."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
from candidates import T

def system_entries(floor=2.0, am=(T(9, 45), T(12, 15)), mid=(T(12, 0), T(14, 30)), use=('AM_H2', 'MID_H3', 'MID_H2'), **kw):
    parts = []
    if 'AM_H2' in use:
        parts.append(setup_entries('H2', win=am, arm_to=am[1] - 15, stop_floor_atr=floor).assign(mod='AM_H2'))
    if 'MID_H3' in use:
        parts.append(setup_entries('H3', win=mid, arm_to=mid[1] - 15, stop_floor_atr=floor, **kw).assign(mod='MID_H3'))
    if 'MID_H2' in use:
        parts.append(setup_entries('H2', win=mid, arm_to=mid[1] - 15, stop_floor_atr=floor).assign(mod='MID_H2'))
    E = pd.concat(parts).sort_values(['e', 'mod'], kind='mergesort').drop_duplicates('e').reset_index(drop=True)
    return E

if __name__ == '__main__':
    for use in (('AM_H2',), ('MID_H3',), ('MID_H2',), ('MID_H3', 'MID_H2'), ('AM_H2', 'MID_H3', 'MID_H2')):
        E = system_entries(use=use)
        for mg, P in (('t45', params(maxbars=45)), ('t60', params(maxbars=60)), ('t90', params(maxbars=90)), ('t120', params(maxbars=120)),
                      ('aggrBE', params(be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25))):
            Tt = run(E, P, cost_pts=0.6)
            ys = {y: round(Tt[Tt.yr == y].pnl.mean(), 3) for y in (2023, 2024, 2025)}
            print('+'.join(use), mg, 'tr/day', round(len(Tt) / 730, 2), 'exp', round(Tt.pnl.mean(), 3), 'net', round(Tt.pnl_net.mean(), 3), ys)
