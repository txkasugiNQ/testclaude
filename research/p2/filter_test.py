"""Context filters (few, logical, continuation-consistent) on the best setups. Per-year drift and bracket EV."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from signals import *
from engine import excursions, outcomes
from drift_test import immediate, T, MID, AM
df = base(); good = df.good.values
A = {k: df[k].values for k in ('high', 'low', 'close', 'open')}; A['sess'] = pd.factorize(df.sess)[0]
c = df.close.values; atr1 = df.atr20.values; sid = A['sess']; n = len(df); vw = df.Vwap_RTH.values
# RTH open (09:30 bar open) per session, known from 09:30 onward
rth_open = df.open.where(df.tod == 570).groupby(df.sess).transform('max').values
def ctx(E):
    s = E.sig.values; d = E.d.values
    E = E.copy()
    E['vwap_al'] = np.sign(c[s] - vw[s]) == d
    E['day_al'] = np.sign(c[s] - rth_open[s]) == d
    # 60-min trend alignment
    j = s - 60; ok = sid[np.maximum(j, 0)] == sid[s]
    E['h1_al'] = ok & (np.sign(c[s] - c[np.maximum(j, 0)]) == d)
    return E
def stats(E, label):
    E = E[good[E.e.values]]
    yr = pd.DatetimeIndex(df.sess.values[E.e.values]).year
    j = np.minimum(E.e.values + 29, n - 1); ok = sid[j] == sid[E.e.values]
    v = np.where(ok, (c[j] - E.entry.values) * E.d.values / atr1[E.sig.values], np.nan)
    R = 2 * atr1[E.sig.values]
    fav, adv, valid, cl = excursions(A, E.e.values, E.d.values, E.entry.values, R, H=120, with_close=True)
    o = outcomes(fav, adv, valid, cl)
    r = {'set': label, 'n/day': len(E) / 730, 'd30': np.nanmean(v), 't': np.nanmean(v) / (np.nanstd(v) / np.sqrt(np.isfinite(v).sum())),
         'ev2x2': o['ev_2.0'].mean(), 'ev2x1': o['ev_1.0'].mean()}
    for y in (2023, 2024, 2025):
        r[f'd30_{y}'] = np.nanmean(v[yr == y]); r[f'ev2x2_{y}'] = o['ev_2.0'][yr == y].mean()
    return r
setups = {
 'H3 MID comp->brk imm': immediate(arms_compression(df, 5, 6, 2.5, 1.0, T(12, 0), T(14, 15)), MID),
 'H3 MID comp->brk pb': entry_machine(df, arms_compression(df, 5, 6, 2.5, 1.0, T(12, 0), T(14, 15), expiry=30), win=MID),
 'H1 MID 15m-IMP imm': immediate(arms_htf_impulse(df, 15, 3, 1.5, T(12, 0), T(14, 15)), MID),
 'H2 AM 5m cluster imm': immediate(arms_htf_impulse(df, 5, 3, 1.5, T(9, 45), T(12, 0), cluster=30), AM),
 'H2c MID 5m cluster imm': immediate(arms_htf_impulse(df, 5, 3, 1.5, T(12, 0), T(14, 15), cluster=30), MID),
}
rows = []
for name, E in setups.items():
    E = ctx(E)
    rows.append(stats(E, name))
    for f in ('vwap_al', 'day_al', 'h1_al'):
        rows.append(stats(E[E[f]], f'  + {f}')); rows.append(stats(E[~E[f]], f'  - NOT {f}'))
R = pd.DataFrame(rows)
pd.set_option('display.width', 300, 'display.max_columns', 40)
print(R.round(3).to_string(index=False))
