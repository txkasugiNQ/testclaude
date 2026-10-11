"""Full evaluation of the final candidate + comparison of management families + walk-forward + plateau + charts."""
import numpy as np, pandas as pd, sys, os, json, itertools
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
from system import system_entries
from candidates import T
from grid import mgmt_grid
OUT = '../output/'
df = get_df()
ALLDAYS = pd.Series(df.sess[df.good].unique())
def ndays(yrs): return int(ALLDAYS.dt.year.isin(yrs).sum())
FINAL_P = params(maxbars=60)
E = system_entries(floor=2.0)
Tt = run(E, FINAL_P, cost_pts=0.6)
Tt['dur'] = Tt.bars

def daily(Tt, yrs):
    days = ALLDAYS[ALLDAYS.dt.year.isin(yrs)]
    g = Tt.groupby('sess')
    D = pd.DataFrame({'pnl': g.pnl.sum(), 'n': g.size()}).reindex(days.values).fillna({'pnl': 0, 'n': 0})
    pos, neg = D.pnl > 1e-9, D.pnl < -1e-9
    def streak(mask):
        s = m = 0
        for v in mask: s = s + 1 if v else 0; m = max(m, s)
        return m
    hit_up = Tt.groupby('sess').apply(lambda x: (x.pnl.cumsum() >= 1).any(), include_groups=False)
    hit_dn = Tt.groupby('sess').apply(lambda x: (x.pnl.cumsum() <= -1).any(), include_groups=False)
    tr_to_up = Tt.groupby('sess').apply(lambda x: (np.argmax(x.pnl.cumsum().values >= 1) + 1) if (x.pnl.cumsum() >= 1).any() else np.nan, include_groups=False)
    return {'days': len(D), 'pos_days%': pos.mean(), 'neg_days%': neg.mean(), 'flat_days%': (~pos & ~neg).mean(),
            '+1R_days%': hit_up.reindex(D.index).fillna(False).mean(), '-1R_days%': hit_dn.reindex(D.index).fillna(False).mean(),
            'avg_daily_R': D.pnl.mean(), 'median_daily_R': D.pnl.median(), 'median_daily_R_tradedays': D.pnl[D.n > 0].median(),
            'max_daily_loss': D.pnl.min(), 'max_daily_gain': D.pnl.max(),
            'max_losing_day_streak': streak(neg.values), 'max_winning_day_streak': streak(pos.values),
            'trades_to_+1R_avg': tr_to_up.mean(), '0_trade_days%': (D.n == 0).mean(), '1_trade_days%': (D.n == 1).mean(),
            '2plus_trade_days%': (D.n >= 2).mean()}, D

def full(Tt, yrs, label):
    t = Tt[Tt.yr.isin(yrs)]
    m = metrics(t, ndays=ndays(yrs))
    d, D = daily(t, yrs)
    nd = ndays(yrs)
    r = {'period': label, **m, 'exp_net(0.6pt)': t.pnl_net.mean(), 'tr/week': len(t) / nd * 5, 'tr/month': len(t) / nd * 21,
         'avg_dur_min': t.bars.mean(), 'med_dur_min': t.bars.median(), 'MAE_med_R': t.mae.median(), 'MAE_p75_R': t.mae.quantile(.75),
         'MFE_med_R': t.mfe.median(), 'MFE_p75_R': t.mfe.quantile(.75), 'R_pts_med': t.Rpts.median(),
         'long_exp': t[t.d > 0].pnl.mean(), 'short_exp': t[t.d < 0].pnl.mean(), 'long_n': int((t.d > 0).sum()), 'short_n': int((t.d < 0).sum()),
         **d}
    return r, D
rows = []; Ds = {}
for label, yrs in (('ALL 2023-25', [2023, 2024, 2025]), ('IS 2023-24', [2023, 2024]), ('OOS 2025', [2025]), ('2023', [2023]), ('2024', [2024])):
    r, D = full(Tt, yrs, label); rows.append(r); Ds[label] = D
F = pd.DataFrame(rows).set_index('period').T
pd.set_option('display.width', 250, 'display.max_rows', 200)
print(F.round(3).to_string())
F.to_csv(OUT + 'p2_final_metrics.csv')
mod = Tt.groupby('mod').agg(n=('pnl', 'size'), exp=('pnl', 'mean'), WR=('pnl', lambda x: (x > 0).mean()))
print(mod.round(3))
by_month = Tt.groupby(pd.PeriodIndex(Tt.sess, freq='M')).pnl.sum()
print('positive months %', (by_month > 0).mean().round(3), 'worst month', by_month.min().round(2), 'best', by_month.max().round(2))
Tt.to_pickle(OUT + 'p2_final_trades.pkl')

# ---- management families on the final entries (IS selection view + OOS) ----
fam_rows = []
for fam, nm, P in mgmt_grid() + [('T time exit', '45bars', params(maxbars=45)), ('T time exit', '90bars', params(maxbars=90))]:
    t = run(E, P, cost_pts=0.6)
    fam_rows.append({'fam': fam, 'mgmt': nm, 'tr/day': len(t) / 730, 'WR': (t.pnl > 1e-9).mean(), 'exp_IS': t[t.yr <= 2024].pnl.mean(),
                     'exp_OOS': t[t.yr == 2025].pnl.mean(), 'exp_net_all': t.pnl_net.mean(), 'avgW': t.pnl[t.pnl > 1e-9].mean(),
                     'avgL': t.pnl[t.pnl < -1e-9].mean(), 'maxLstreak': metrics(t)['maxLstreak']})
FR = pd.DataFrame(fam_rows); FR.to_csv(OUT + 'p2_mgmt_families_final.csv', index=False)
print(FR.groupby('fam')[['tr/day', 'WR', 'exp_IS', 'exp_OOS', 'exp_net_all']].agg(['mean', 'max']).round(3).to_string())
print(FR.sort_values('WR', ascending=False).head(8).round(3).to_string(index=False))

# ---- walk-forward of the selection (floor x mgmt) for the system ----
MG = {'t45': params(maxbars=45), 't60': params(maxbars=60), 't90': params(maxbars=90), 't120': params(maxbars=120),
      'aggrBE0.2': params(be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25), 'BE1.5+.5 t90': params(maxbars=90, be_trig=1.5, be_off=0.5),
      'p33@.5 t60': params(maxbars=60, pfrac=0.33, ptp=0.5), 'swing10@1': params(tr_type=4, tr_act=1.0, tr_dist=10, maxbars=120)}
trades = {}
for fl in (1.5, 2.0, 2.5, 3.0):
    Ef = system_entries(floor=fl)
    for k, P in MG.items():
        t = run(Ef, P, cost_pts=0.6); t['q'] = pd.PeriodIndex(t.sess, freq='Q'); trades[(fl, k)] = t
wf, picks = [], []
for q in pd.period_range('2024Q1', '2025Q4', freq='Q'):
    bk = max(trades, key=lambda k: trades[k][trades[k].q < q].pnl.mean())
    te = trades[bk][trades[bk].q == q]; wf.append(te)
    picks.append({'quarter': str(q), 'picked': str(bk), 'train_exp': trades[bk][trades[bk].q < q].pnl.mean(), 'test_exp': te.pnl.mean(), 'n': len(te)})
WF = pd.concat(wf); P_ = pd.DataFrame(picks)
print(P_.round(3).to_string(index=False))
wfm = metrics(WF, ndays=ndays([2024, 2025]))
print('WF OOS:', {k: round(float(v), 3) for k, v in wfm.items()}, 'net', round(WF.pnl_net.mean(), 3))
P_.to_csv(OUT + 'p2_wf_picks.csv', index=False)
json.dump({k: float(v) for k, v in wfm.items()} | {'net': float(WF.pnl_net.mean())}, open(OUT + 'p2_wf_summary.json', 'w'))
# rolling 6-month windows of fixed candidate
roll = Tt.set_index('sess').pnl
h = roll.groupby(pd.PeriodIndex(roll.index, freq='Q')).agg(['mean', 'size'])
print('per quarter exp:\n', h.round(3).T.to_string())
h.to_csv(OUT + 'p2_final_quarters.csv')

# ---- plateau: windows, floor, time exit ----
pl = []
for amS, midS in itertools.product((T(9, 30), T(9, 45), T(10, 0)), (T(11, 45), T(12, 0), T(12, 15))):
    for amL, midL in ((150, 150), (120, 150), (150, 120), (180, 180)):
        Ev = system_entries(floor=2.0, am=(amS, amS + amL), mid=(midS, midS + midL))
        t = run(Ev, FINAL_P)
        pl.append({'AM': f'{amS//60}:{amS%60:02d}+{amL}', 'MID': f'{midS//60}:{midS%60:02d}+{midL}', 'tr/day': len(t) / 730,
                   'exp': t.pnl.mean(), '2023': t[t.yr == 2023].pnl.mean(), '2024': t[t.yr == 2024].pnl.mean(), '2025': t[t.yr == 2025].pnl.mean()})
PL = pd.DataFrame(pl); PL.to_csv(OUT + 'p2_plateau_windows.csv', index=False)
print(PL.round(3).to_string(index=False))
pf = []
for fl in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
    for mb in (30, 45, 60, 75, 90, 120):
        t = run(system_entries(floor=fl), params(maxbars=mb))
        pf.append({'floor': fl, 'maxbars': mb, 'exp': t.pnl.mean(), 'min_year': min(t[t.yr == y].pnl.mean() for y in (2023, 2024, 2025))})
PF = pd.DataFrame(pf); PF.to_csv(OUT + 'p2_plateau_floor_time.csv', index=False)
print(PF.pivot(index='floor', columns='maxbars', values='exp').round(3)); print(PF.pivot(index='floor', columns='maxbars', values='min_year').round(3))
# cost sensitivity
for cpt in (0, 0.5, 1.0, 1.5, 2.0):
    print('cost', cpt, 'pts RT -> exp', round((Tt.pnl - cpt / Tt.Rpts).mean(), 3))
