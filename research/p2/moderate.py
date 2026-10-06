import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
E = setup_entries('H3', stop_floor_atr=2.0)
MG = {}
for mb in (60, 90):
    MG[f't{mb} pure'] = params(maxbars=mb)
    for bt in (0.5, 1.0, 1.5): MG[f't{mb} BE@{bt}'] = params(maxbars=mb, be_trig=bt)
    for bt, bo in ((1.0, 0.25), (1.5, 0.5)): MG[f't{mb} BE@{bt}+{bo}'] = params(maxbars=mb, be_trig=bt, be_off=bo)
    for pf, pt in ((0.5, 1.0), (0.33, 0.5), (0.5, 0.5), (0.5, 1.5)): MG[f't{mb} part{pf}@{pt} noBE'] = params(maxbars=mb, pfrac=pf, ptp=pt)
    MG[f't{mb} ATRtrail3@1.5'] = params(maxbars=mb, tr_type=2, tr_act=1.5, tr_dist=3)
    MG[f't{mb} swing10@1.5'] = params(maxbars=mb, tr_type=4, tr_act=1.5, tr_dist=10)
    MG[f't{mb} tp3'] = params(maxbars=mb, tp=3)
    MG[f't{mb} tp2'] = params(maxbars=mb, tp=2)
rows = []
for k, P in MG.items():
    Tt = run(E, P, cost_pts=0.6)
    r = {'mgmt': k}
    for per, f in (('IS', Tt.yr <= 2024), ('OOS25', Tt.yr == 2025)):
        m = metrics(Tt[f]); r[f'exp_{per}'] = m['exp']; r[f'WR_{per}'] = m['WR']
    r['2023'] = Tt[Tt.yr == 2023].pnl.mean(); r['2024'] = Tt[Tt.yr == 2024].pnl.mean()
    m = metrics(Tt); r.update({'avgW': m['avgW'], 'avgL': m['avgL'], 'PF': m['PF'], 'maxDD': m['maxDD'], 'maxLstreak': m['maxLstreak']})
    rows.append(r)
pd.set_option('display.width', 250)
print(pd.DataFrame(rows).round(3).to_string(index=False))
