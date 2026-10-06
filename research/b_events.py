"""Phase B: generic continuation events + control baseline -> first-passage outcomes.
Signals evaluated at CLOSE of bar t, entry at OPEN of bar t+1 (no look-ahead).
"""
import numpy as np, pandas as pd
from prep import load, TICK
from engine import excursions, outcomes

df = load()
A = {k: df[k].values for k in ('open', 'high', 'low', 'close', 'atr20')}
A['sess'] = df.sess.values.astype('datetime64[D]').astype(np.int64)
o, h, l, c, atr, sess = A['open'], A['high'], A['low'], A['close'], A['atr20'], A['sess']
n = len(df)
good = df.good.values

def lag(a, k):
    out = np.full(n, np.nan); out[k:] = a[:-k]
    same = np.zeros(n, bool); same[k:] = sess[k:] == sess[:-k]
    out[~same] = np.nan; return out

def roll_max(a, w):  # max over a[t-w+1..t]
    return pd.Series(a).rolling(w).max().values
def roll_min(a, w):
    return pd.Series(a).rolling(w).min().values

# ---- generic triggers (direction arrays: +1/-1/0) ----
sig = {}
mv5 = c - lag(c, 5)
sig['IMP'] = np.where(mv5 >= 2.0 * atr, 1, np.where(mv5 <= -2.0 * atr, -1, 0))
hh20 = lag(roll_max(h, 20), 1); ll20 = lag(roll_min(l, 20), 1)
sig['BRK'] = np.where((c > hh20) & (lag(c, 1) <= hh20), 1, np.where((c < ll20) & (lag(c, 1) >= ll20), -1, 0))
mv15 = c - lag(c, 15)
pb_l = (lag(c, 1) < lag(o, 1)) & (c > lag(h, 1)) & (mv15 >= 2.0 * atr)
pb_s = (lag(c, 1) > lag(o, 1)) & (c < lag(l, 1)) & (mv15 <= -2.0 * atr)
sig['PB'] = np.where(pb_l, 1, np.where(pb_s, -1, 0))

def refractory(s, k=5):
    s = s.copy(); last = -10**9
    nz = np.flatnonzero(s)
    keep = np.zeros(n, bool); prev = -10**9
    for i in nz:
        if i - prev > k: keep[i] = True; prev = i
    s[~keep] = 0; return s
for k in sig: sig[k] = refractory(sig[k])

lo3 = roll_min(l, 3); hi3 = roll_max(h, 3)

def build(t, d, name):
    t = np.asarray(t); d = np.asarray(d)
    e = t + 1
    ok = (e < n) & good[t]
    ok[ok] &= sess[e[ok]] == sess[t[ok]]
    ok &= ~np.isnan(atr[t])
    t, d, e = t[ok], d[ok], e[ok]
    entry = o[e]
    rows = []
    for stop_kind in ('struct', 'atr1'):
        if stop_kind == 'struct':
            stop = np.where(d > 0, lo3[t] - TICK, hi3[t] + TICK)
            R = (entry - stop) * d
        else:
            R = atr[t] * 1.0
        keep = R > 0
        res = {}
        CH = 200000
        for s0 in range(0, keep.sum(), CH):
            sl = np.flatnonzero(keep)[s0:s0 + CH]
            fav, adv, valid = excursions(A, e[sl], d[sl], entry[sl], R[sl])
            out = outcomes(fav, adv, valid)
            for k, v in out.items(): res.setdefault(k, []).append(v)
        res = {k: np.concatenate(v) for k, v in res.items()}
        sl = np.flatnonzero(keep)
        tab = pd.DataFrame(res)
        tab['t'] = t[sl]; tab['d'] = d[sl]; tab['R_pts'] = R[sl]; tab['R_atr'] = R[sl] / atr[t[sl]]
        tab['stop'] = stop_kind; tab['trig'] = name
        rows.append(tab)
    return pd.concat(rows)

tabs = []
for name, s in sig.items():
    t = np.flatnonzero(s); tabs.append(build(t, s[t], name)); print(name, len(t))
# control: every bar, both directions
allt = np.flatnonzero(good)
for dd in (1, -1):
    tabs.append(build(allt, np.full(len(allt), dd), f'CTRL'))
T = pd.concat(tabs, ignore_index=True)
T['etod'] = df.tod.values[T.t + 1]
T['sess'] = df.sess.values[T.t]
T['yr'] = pd.DatetimeIndex(T.sess).year
for col in T.columns:
    if T[col].dtype == np.int64 and col.startswith('t_'): T[col] = T[col].astype(np.int16)
T.to_pickle('output/B_events.pkl')
print(T.groupby(['trig', 'stop']).size())
print(T.groupby(['trig', 'stop']).R_atr.median())
