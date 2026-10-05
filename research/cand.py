"""Candidate A: session-extreme breakout aligned with daily trend."""
import numpy as np, pandas as pd
from lab import *
def daily_regime(b, w=50, kind='ma'):
    d = b.days.copy()
    d = d[d.rth_c.notna() & (d.n_pm >= 200)]          # valid RTH sessions only
    if kind == 'ma':
        ma = d.rth_c.rolling(w).mean()
        reg = np.sign(d.rth_c - ma).shift(1)          # known before today's session
    elif kind == 'ret':
        reg = np.sign(d.rth_c - d.rth_c.shift(w)).shift(1)
    elif kind == 'ema':
        ma = d.rth_c.ewm(span=w, adjust=False).mean()
        reg = np.sign(d.rth_c - ma).shift(1)
    return pd.Series(b.tdate).map(reg).values

def signals_A(b, stopk=1.0, w=50, kind='ma', win=(720, 840), etype='brk', min_bars_since=0, stop_mode='atr', swing_n=5):
    S = pd.Series; day = b.day; tod = b.tod; c,h,l,atr = b.c,b.h,b.l,b.atr
    L = daylevels(b)
    rh = S(L['rh']).values; rl = S(L['rl']).values      # running RTH high/low INCLUDING current bar
    reg = daily_regime(b, w, kind)
    ok = (tod >= win[0] - b.tf) & (tod < win[1]) & np.isfinite(reg)
    rows = []
    for side in (1, -1):
        X = rh if side > 0 else rl                      # level known at close of bar i: current session extreme
        if etype == 'brk':
            # stop order 1 tick beyond current session extreme, valid for next bar
            cond = ok & (reg == side)
            idx = np.where(cond)[0]
            e = X[idx] + side*0.25
        if stop_mode == 'atr':
            sl = e - side*stopk*atr[idx]
        elif stop_mode == 'swing':   # lowest low of last swing_n bars
            lo = S(l).groupby(day).transform(lambda s: s.rolling(swing_n, min_periods=1).min()).values
            hi = S(h).groupby(day).transform(lambda s: s.rolling(swing_n, min_periods=1).max()).values
            sl = (lo[idx] - 0.25) if side > 0 else (hi[idx] + 0.25)
        rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=1, eprice=e, sl=sl, expiry=1)))
    s = pd.concat(rows)
    s = s[(s.eprice - s.sl)*s.side >= 3]
    return s
