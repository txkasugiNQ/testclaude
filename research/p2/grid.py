"""Management grid on IS (2023-2024) for the main setup(s). Daily +-1R limit always on."""
import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *

def mgmt_grid():
    G = []
    for tp in (0.5, 1, 1.5, 2, 3):
        G.append(('A bracket', f'tp{tp}', params(tp=tp)))
    for bt, bo, ta, td in itertools.product((0.15, 0.2, 0.25, 0.3, 0.4), (0, 0.05, 0.1), (0.3, 0.5), (0.25, 0.5)):
        G.append(('B BE+fixedR trail', f'be{bt}+{bo} act{ta} d{td}', params(be_trig=bt, be_off=bo, tr_type=1, tr_act=ta, tr_dist=td)))
    for bt in (0, 0.2, 0.5):
        for ta, td in itertools.product((0.5, 1.0), (1, 2, 3)):
            G.append(('C ATR trail', f'be{bt} act{ta} {td}ATR', params(be_trig=bt, tr_type=2, tr_act=ta, tr_dist=td)))
    for bt in (0, 0.2, 0.5):
        for ta in (0.3, 0.5, 1.0):
            G.append(('D candle trail', f'be{bt} act{ta}', params(be_trig=bt, tr_type=3, tr_act=ta)))
            for nb in (3, 5, 10):
                G.append(('E swing trail', f'be{bt} act{ta} n{nb}', params(be_trig=bt, tr_type=4, tr_act=ta, tr_dist=nb)))
    for bt, a1, d1, a2, d2 in ((0.2, 0.4, 0.4, 0.6, 0.25), (0.2, 0.4, 0.5, 1.0, 0.3), (0.3, 0.5, 0.5, 1.0, 0.4), (0.5, 1.0, 0.75, 1.5, 0.5), (0.0, 1.0, 1.0, 2.0, 0.75)):
        G.append(('H hybrid', f'be{bt} t{a1}/{d1} t{a2}/{d2}', params(be_trig=bt, tr_type=1, tr_act=a1, tr_dist=d1, s2_trig=a2, s2_dist=d2)))
    for pf, pt in itertools.product((0.5,), (0.3, 0.5, 1.0)):
        for run_ in ('tp2', 'tp3', 'atr2', 'be_only'):
            kw = dict(pfrac=pf, ptp=pt, be_trig=pt, be_off=0.0)
            if run_ == 'tp2': kw['tp'] = 2
            if run_ == 'tp3': kw['tp'] = 3
            if run_ == 'atr2': kw.update(tr_type=2, tr_act=1.0, tr_dist=2)
            G.append(('J partial+runner', f'{pf}@{pt} {run_}', params(**kw)))
    for mb in (30, 60, 120):
        G.append(('T time exit', f'{mb}bars', params(maxbars=mb)))
    return G

if __name__ == '__main__':
    setup = sys.argv[1] if len(sys.argv) > 1 else 'H3'
    rows = []
    for floor in (0.0, 1.0, 1.5, 2.0, 3.0):
        E = setup_entries(setup, stop_floor_atr=floor)
        E_is = E[YR[E.e.values] <= 2024]
        for fam, nm, P in mgmt_grid():
            T = run(E_is, P, cost_pts=0.6)
            r = {'floor': floor, 'fam': fam, 'mgmt': nm, **metrics(T, ndays=517), 'exp_net': T.pnl_net.mean(), 'Rpts': T.Rpts.median()}
            rows.append(r)
        print('floor', floor, flush=True)
    R = pd.DataFrame(rows); R.to_csv(f'../output/p2_grid_IS_{setup}.csv', index=False)
    pd.set_option('display.width', 300, 'display.max_rows', 300)
    cols = ['floor', 'fam', 'mgmt', 'tr/day', 'WR', 'BE%', 'avgW', 'avgL', 'exp', 'exp_net', 'PF', 'maxDD', 'maxLstreak', 'Rpts']
    print(R.groupby(['floor', 'fam']).exp.agg(['mean', 'max', 'min']).round(3).unstack(0).to_string())
    print(R.sort_values('exp', ascending=False)[cols].head(30).round(3).to_string(index=False))
