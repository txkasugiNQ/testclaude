import numpy as np, pandas as pd
from lab import *
def more_levels(b):
    """additional per-bar levels known at bar close"""
    L = daylevels(b)
    tod = b.tod; day = b.day
    S = pd.Series
    # IB (9:30-10:30)
    ib = (tod > 570) & (tod <= 630)
    L['ibh'] = S(np.where(ib, b.h, -np.inf)).groupby(day).cummax().values
    L['ibl'] = S(np.where(ib, b.l, np.inf)).groupby(day).cummin().values
    L['ibh'] = np.where(tod > 630, L['ibh'], np.nan); L['ibl'] = np.where(tod > 630, L['ibl'], np.nan)
    # lunch range 12:00-13:30, available after 13:30
    lu = (tod > 720) & (tod <= 810)
    lh = S(np.where(lu, b.h, -np.inf)).groupby(day).cummax().values
    ll = S(np.where(lu, b.l, np.inf)).groupby(day).cummin().values
    L['luh'] = np.where(tod > 810, lh, np.nan); L['lul'] = np.where(tod > 810, ll, np.nan)
    # PM open (12:00 price) = close of bar at 12:00
    p12 = S(np.where(tod == 720, b.c, np.nan)).groupby(day).transform('max').values
    L['p12'] = np.where(tod >= 720, p12, np.nan)
    # VWAP bands using 1m data of the TF bars (approx with TF bars: typical price * volume)
    rth = tod > 570
    tp = (b.h + b.l + b.c)/3
    v = np.where(rth, b.v, 0.0)
    cv = S(v).groupby(day).cumsum().values
    cpv = S(v*tp).groupby(day).cumsum().values
    cp2v = S(v*tp*tp).groupby(day).cumsum().values
    vw = np.where(cv>0, cpv/np.maximum(cv,1), np.nan)
    sd = np.sqrt(np.maximum(cp2v/np.maximum(cv,1) - vw**2, 0))
    L['vw'] = b.vw; L['vsd'] = sd
    for k in (1, 2, 3):
        L[f'vwu{k}'] = b.vw + k*sd; L[f'vwd{k}'] = b.vw - k*sd
    # AM POC (price bin with highest volume 9:30-12:00), bin=5pts; available after 12:00
    am = (tod > 570) & (tod <= 720)
    poc = np.full(len(tod), np.nan)
    df = pd.DataFrame(dict(day=day, bin=(np.round(tp/5)*5), v=np.where(am, b.v, 0)))
    g = df[am].groupby(['day','bin']).v.sum().reset_index()
    pp = g.loc[g.groupby('day').v.idxmax()].set_index('day').bin
    poc = S(day).map(pp).values
    L['poc'] = np.where(tod > 720, poc, np.nan)
    L['pdc'] = L['pdc']; L['ro'] = L['ro']
    # previous day's PM... skip
    # day mid
    L['mid'] = (L['rh'] + L['rl'])/2
    return L
if __name__ == '__main__':
    b = B(2); L = more_levels(b)
    pm = (b.tod>720)
    for k in ['ibh','luh','p12','vsd','vwu2','poc','mid']:
        print(k, np.nanmean(L[k][pm]))
    print('vsd mean PM', np.nanmean(L['vsd'][pm]), 'atr mean', b.atr[pm].mean())
