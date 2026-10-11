import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from slots import *
from sim import params
def hm(s): a, b = s.split(':'); return int(a) * 60 + int(b)
MG = {}
for H in (60, 90, 120):
    MG[f'time{H}'] = params(maxbars=H)
    for m, a in ((3, 0.0), (5, 0.0), (5, 0.5), (8, 0.0), (8, 1.0), (12, 0.0)):
        MG[f'ATR{m}@{a} t{H}'] = params(maxbars=H, tr_type=2, tr_dist=m, tr_act=a)
    for dist, a in ((0.5, 1.0), (1.0, 1.0), (0.75, 0.5)):
        MG[f'R{dist}@{a} t{H}'] = params(maxbars=H, tr_type=1, tr_dist=dist, tr_act=a)
    MG[f'BE@1 t{H}'] = params(maxbars=H, be_trig=1.0)
    MG[f'swing20@0.5 t{H}'] = params(maxbars=H, tr_type=4, tr_dist=20, tr_act=0.5)
    MG[f'hyb t{H}'] = params(maxbars=H, be_trig=0.5, tr_type=1, tr_act=1.0, tr_dist=0.75, s2_trig=2.0, s2_dist=0.5)
    MG[f'aggrBE.2 t{H}'] = params(maxbars=H, be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25)
slots = {'AM_L60': ('L60', ['09:50', '09:55', '10:00', '10:05', '10:10', '10:15', '10:20', '10:25', '10:30', '10:35']),
         'AM_RTH': ('RTH', ['09:50', '10:00', '10:10', '10:15', '10:20', '10:25', '10:30']),
         'MID_RTH': ('RTH', ['12:30', '12:35', '12:40', '12:45', '12:50', '12:55', '13:00', '13:05', '13:10', '13:15', '13:20']),
         'MID_L30': ('L30', ['12:45', '12:50', '12:55', '13:00', '13:05', '13:10'])}
rows = []
for sname, (anc, times) in slots.items():
    for t in times:
        for k in (0.05, 0.075, 0.1, 0.15, 0.2):
            E = slot_entries(hm(t), anc, k=k)
            for mg, P in MG.items():
                Tt = run(E, P)
                r = {'slot': sname, 'T': t, 'k': k, 'mgmt': mg, 'n': len(Tt), 'exp': Tt.pnl.mean(), 'WR': (Tt.pnl > 1e-9).mean(),
                     'Rpts': Tt.Rpts.median()}
                for y in (2023, 2024, 2025): r[y] = Tt[Tt.yr == y].pnl.mean()
                r['IS'] = Tt[Tt.yr <= 2024].pnl.mean(); r['net'] = Tt.pnl_net.mean()
                rows.append(r)
    print(sname, flush=True)
R = pd.DataFrame(rows); R['min_y'] = R[[2023, 2024, 2025]].min(axis=1)
R.to_pickle('../output/p3_slot_grid.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 300)
# robust aggregation over the time plateau: average across T within slot
A = R.groupby(['slot', 'k', 'mgmt']).agg(exp=('exp', 'mean'), IS=('IS', 'mean'), y2025=(2025, 'mean'), min_y_mean=('min_y', 'mean'),
                                          worstT_IS=('IS', 'min'), WR=('WR', 'mean'), Rpts=('Rpts', 'mean')).reset_index()
for s in slots:
    a = A[A.slot == s].sort_values('IS', ascending=False)
    print(f'===== {s}: top by IS (averaged over all entry times of the plateau)')
    print(a.head(15).round(3).to_string(index=False))
    print(a[a.mgmt.str.startswith('aggr')].sort_values('IS', ascending=False).head(3).round(3).to_string(index=False))
