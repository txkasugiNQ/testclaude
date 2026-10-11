"""Phase A: time-of-day profile of NQ continuation vs mean-reversion behaviour.
All x/y measured in units of causal ATR20 (1-min) at time t; only intra-session pairs.
"""
import numpy as np, pandas as pd
from prep import load

df = load()
c = df.close.values; atr = df.atr20.values; sess = df.sess.values; smin = df.smin.values
n = len(df)
def shift(a, k):  # a[t+k] (k may be negative), nan if crosses session
    out = np.full(n, np.nan)
    if k > 0:
        out[:-k] = a[k:]; same = np.zeros(n, bool); same[:-k] = sess[k:] == sess[:-k]
    else:
        k = -k; out[k:] = a[:-k]; same = np.zeros(n, bool); same[k:] = sess[:-k] == sess[k:]
    out[~same] = np.nan
    return out

rows = []
df['bucket'] = (df.tod // 5) * 5
df['yr'] = df.sess.dt.year
res = {}
for L in (5, 15):
    x = (c - shift(c, -L)) / atr
    for H in (5, 15, 30):
        y = (shift(c, H) - c) / atr
        res[(L, H)] = (x, y)

def agg(mask):
    out = {}
    b = df.bucket.values[mask]
    for (L, H), (x, y) in res.items():
        xx, yy = x[mask], y[mask]
        ok = ~np.isnan(xx) & ~np.isnan(yy)
        t = pd.DataFrame({'b': b[ok], 'x': xx[ok], 'y': yy[ok]})
        thr = np.nanquantile(np.abs(t.x), 0.8)
        t['big'] = np.abs(t.x) >= thr
        t['cont'] = np.sign(t.x) * t.y
        g = t.groupby('b')
        beta = g.apply(lambda s: np.cov(s.x, s.y)[0, 1] / np.var(s.x), include_groups=False)
        gb = t[t.big].groupby('b')
        out[f'beta_L{L}H{H}'] = beta
        out[f'cont_L{L}H{H}'] = gb.cont.mean()          # mean signed follow-through (ATR units) after big moves
        out[f'pcont_L{L}H{H}'] = gb.cont.apply(lambda s: (s > 0).mean())
    # vol / volume / variance ratio(15)
    d = df[mask]
    out['tr_pts'] = d.groupby('bucket').tr.mean()
    out['volume'] = d.groupby('bucket').volume.mean()
    r1 = (np.r_[np.nan, np.diff(c)] / atr)[mask]
    r1[np.r_[True, sess[1:] != sess[:-1]][mask]] = np.nan
    x15, y15 = res[(15, 15)]
    v15 = pd.Series(y15[mask]).groupby(d.bucket.values).var()
    v1 = pd.Series(r1).groupby(d.bucket.values).var()
    out['VR15'] = v15 / (15 * v1)
    return pd.DataFrame(out)

good = df.good.values
IS = good & (df.yr.values <= 2024)
OOS = good & (df.yr.values == 2025)
A_is, A_oos = agg(IS), agg(OOS)
A_is.to_csv('output/A_profile_IS.csv'); A_oos.to_csv('output/A_profile_OOS.csv')
pd.set_option('display.width', 250, 'display.max_rows', 400)
cols = ['tr_pts', 'beta_L5H5', 'beta_L15H15', 'beta_L15H30', 'cont_L5H15', 'pcont_L5H15', 'cont_L15H30', 'VR15']
show = A_is[cols].copy(); show.index = [f'{i//60:02d}:{i%60:02d}' for i in show.index]
print(show.round(3).to_string())
print('IS vs OOS corr of profiles:')
for k in cols: print(k, round(A_is[k].corr(A_oos[k]), 3))
