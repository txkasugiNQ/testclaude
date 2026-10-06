"""Phase G: candidate windows head-to-head + plateau neighbours.
Uses IMP (5-bar impulse >=2 ATR) and PB (pullback-resumption with 15-bar trend >=2 ATR) events,
1-ATR fixed stop for comparability, plus control (all bars, both directions).
"""
import numpy as np, pandas as pd
from prep import load
from engine import excursions
df = load()
T = pd.read_pickle('output/B_events.pkl')
T['sm'] = (T.etod - 18*60) % 1440
def sm(hhmm): h, m = map(int, hhmm.split(':')); return (h*60+m - 18*60) % 1440
CANDS = {'Globex reopen 18:00-19:30': ('18:00', 90), 'Asia 22:00-00:30': ('22:00', 150),
         'Europe/London 01:00-04:30': ('01:00', 210), 'London late 05:00-07:00': ('05:00', 120),
         'Pre-NY 07:00-09:30': ('07:00', 150), 'NY open 09:30-11:00': ('09:30', 90),
         'NY late morning 11:00-12:30': ('11:00', 90), 'NY early PM 12:30-14:30': ('12:30', 120),
         'NY late PM 14:30-16:00': ('14:30', 90)}
A = {k: df[k].values for k in ('high', 'low')}; A['sess'] = df.sess.values.astype('datetime64[D]').astype(np.int64)
o = df.open.values; atr = df.atr20.values
ndays = T[T.trig == 'CTRL'].groupby('yr').sess.nunique()

def window(g, s, L): return g[(g.sm >= s) & (g.sm < s + L)]

def path_stats(g):
    """recompute paths for MAE-before-+2R and time-in-ATR for 'good' continuation trades"""
    e = g.t.values + 1; d = g.d.values; ent = o[e]; R = atr[g.t.values]
    fav, adv, valid = excursions(A, e, d, ent, R, H=60)
    H = 60; j = np.arange(H)[None, :]
    def first(m): return np.where(m.any(1), m.argmax(1), H)
    t2 = first(fav >= 2.0)
    mae2 = np.where((j <= t2[:, None]) & valid, adv, -np.inf).max(1)
    good = t2 < H
    return mae2[good], t2[good]

rows = []
for name, (st, L) in CANDS.items():
    s = sm(st)
    for trig in ('IMP', 'PB'):
        g = window(T[(T.trig == trig) & (T.stop == 'atr1')], s, L)
        cg = window(T[(T.trig == 'CTRL') & (T.stop == 'atr1')], s, L)
        r = {'window': name, 'trig': trig, 'n/day': len(g) / ndays.sum()}
        for a in (0.25, 0.5, 1.0):
            r[f'P+{a}'] = g[f'win_{a}'].mean(); r[f'edge+{a}'] = g[f'win_{a}'].mean() - cg[f'win_{a}'].mean()
        for y in (2023, 2024, 2025):
            gy, cy = g[g.yr == y], cg[cg.yr == y]
            r[f'edge.5_{y}'] = gy['win_0.5'].mean() - cy['win_0.5'].mean()
        w = g[g['win_0.5']]
        r['med_bars_to_+0.25'] = g.loc[g['win_0.25'], 't_0.25'].median() + 1
        r['med_bars_to_+0.5'] = w['t_0.5'].median() + 1
        r['med_bars_to_+1'] = g.loc[g['win_1.0'], 't_1.0'].median() + 1
        r['fe30'] = (g.mfe30 - g.mae30).mean() - (cg.mfe30 - cg.mae30).mean()
        r['MFE30_med'] = g.mfe30.median(); r['MAE30_med'] = g.mae30.median()
        r['MAEpre+1R_p50'] = g.loc[g['t_1.0'] < 60, 'mae_pre_1R'].median()
        r['MAEpre+1R_p75'] = g.loc[g['t_1.0'] < 60, 'mae_pre_1R'].quantile(.75)
        mae2, t2 = path_stats(g)
        r['share_reach+2ATR'] = len(mae2) / len(g)
        r['MAEpre+2_p50'] = np.median(mae2); r['MAEpre+2_p75'] = np.quantile(mae2, .75); r['MAEpre+2_p90'] = np.quantile(mae2, .9)
        r['bars_to_+2_med'] = np.median(t2) + 1
        r['ATR_pts'] = atr[g.t.values].mean()
        rows.append(r)
R = pd.DataFrame(rows)
pd.set_option('display.width', 300, 'display.max_columns', 50)
print(R.round(3).T.to_string())
R.to_csv('output/G_candidates.csv', index=False)

# --- efficiency ratio / chop per window per year (market noise) ---
d = df[df.good].copy(); d['yr'] = d.sess.dt.year
out = []
for name, (st, L) in CANDS.items():
    s = sm(st)
    w = d[(d.smin >= s) & (d.smin < s + L)]
    g = w.groupby('sess')
    net = (g.close.last() - g.open.first()).abs()
    path = g.apply(lambda x: x.close.diff().abs().sum() + abs(x.close.iloc[0] - x.open.iloc[0]), include_groups=False)
    er = net / path
    rng = (g.high.max() - g.low.min())
    atrw = g.atr20.mean()
    flips = g.apply(lambda x: (np.sign(x.close - x.open).diff().abs() == 2).mean(), include_groups=False)
    yrs = pd.DatetimeIndex(er.index).year
    out.append({'window': name, 'ER_mean': er.mean(), 'ER_2023': er[yrs == 2023].mean(), 'ER_2024': er[yrs == 2024].mean(),
                'ER_2025': er[yrs == 2025].mean(), 'ER_rw_expect': np.sqrt(2/np.pi/L),
                'range/ATR': (rng/atrw).mean(), 'range/(ATR*sqrtL)': (rng/atrw/np.sqrt(L)).mean(), 'bar_flip_rate': flips.mean(),
                'range_pts_med': rng.median()})
E = pd.DataFrame(out)
print(E.round(3).to_string(index=False))
E.to_csv('output/G_noise.csv', index=False)
