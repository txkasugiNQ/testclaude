import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from rthbreak import rth_break_entries
from orb import run, params
def MGS():
    G = {'eod': params(maxbars=1000)}
    for H in (60, 120, 180, 240): G[f'time{H}'] = params(maxbars=H)
    for m in (5, 8, 12, 20, 30):
        for a in (0.0, 1.0): G[f'ATR{m}@{a}'] = params(maxbars=1000, tr_type=2, tr_dist=m, tr_act=a)
    for dist, a in itertools.product((0.5, 1.0, 1.5, 2.0), (0.5, 1.0, 2.0)): G[f'R{dist}@{a}'] = params(maxbars=1000, tr_type=1, tr_dist=dist, tr_act=a)
    for n in (10, 20, 30, 60): G[f'swing{n}@1'] = params(maxbars=1000, tr_type=4, tr_dist=n, tr_act=1.0)
    for bt in (0.5, 1.0, 2.0): G[f'BE@{bt}'] = params(maxbars=1000, be_trig=bt)
    for pt in (1.0, 2.0): G[f'part50@{pt}+BE'] = params(maxbars=1000, pfrac=0.5, ptp=pt, be_trig=pt)
    G['part50@1+R1@2'] = params(maxbars=1000, pfrac=0.5, ptp=1.0, tr_type=1, tr_dist=1.0, tr_act=2.0)
    G['hyb BE1 R1@2 R0.5@4'] = params(maxbars=1000, be_trig=1.0, tr_type=1, tr_act=2.0, tr_dist=1.0, s2_trig=4.0, s2_dist=0.5)
    G['hyb R1.5@1 R1@3'] = params(maxbars=1000, tr_type=1, tr_act=1.0, tr_dist=1.5, s2_trig=3.0, s2_dist=1.0)
    G['aggrBE.2'] = params(maxbars=1000, be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25)
    G['BE.3+trail.5'] = params(maxbars=1000, be_trig=0.3, be_off=0.05, tr_type=1, tr_act=0.5, tr_dist=0.5)
    for tp in (1, 2, 3, 5): G[f'tp{tp}'] = params(maxbars=1000, tp=tp)
    return G
if __name__ == '__main__':
    rows = []
    for intact in (True, False):
        for k in (0.08, 0.1, 0.12, 0.15, 0.2):
            E = rth_break_entries('02:00', '08:00', '11:00', k=k, intact=intact)
            for mg, P in MGS().items():
                Tt = run(E, P)
                r = {'intact': intact, 'k': k, 'mgmt': mg, 'n/day': len(Tt) / 730, 'WR': (Tt.pnl > 1e-9).mean(),
                     'IS': Tt[Tt.yr <= 2024].pnl.mean(), 'OOS': Tt[Tt.yr == 2025].pnl.mean(), 'exp': Tt.pnl.mean(), 'net': Tt.pnl_net.mean(),
                     'avgW': Tt.pnl[Tt.pnl > 1e-9].mean(), 'avgL': Tt.pnl[Tt.pnl < -1e-9].mean(), 'Rpts': Tt.Rpts.median(), 'dur': Tt.bars.mean()}
                for y in (2023, 2024): r[y] = Tt[Tt.yr == y].pnl.mean()
                rows.append(r)
    R = pd.DataFrame(rows); R['min_y'] = R[[2023, 2024, 'OOS']].min(axis=1)
    R.to_pickle('../output/p3_mgmt_ldn.pkl')
    pd.set_option('display.width', 250, 'display.max_rows', 400)
    for it in (True, False):
        s = R[R.intact == it]
        fam = s.assign(f=s.mgmt.str.extract(r'^([A-Za-z]+)')[0]).groupby('f')[['IS', 'OOS', 'WR']].mean().round(3)
        print(f'==== intact={it}, family means over k:'); print(fam.sort_values('IS', ascending=False).to_string())
        print(s.sort_values('IS', ascending=False).head(20).round(3).to_string(index=False))
        print('-- highest WR with OOS>0.15:'); print(s[s.OOS > 0.15].sort_values('WR', ascending=False).head(12).round(3).to_string(index=False))
