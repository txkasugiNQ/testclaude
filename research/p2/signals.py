"""Phase 2 signal generation (no look-ahead).

All setups share ONE entry machine ("pullback-resumption"):
  An ARM event (time a, direction d) says: a higher-timeframe continuation context exists.
  From 1-min bar a onward (until expiry), for a long:
    run_max = highest high of the impulse (HTF bar) and anything after it
    a PULLBACK = >=1 completed 1m bar after run_max with high < run_max, depth = run_max - pullback_low >= dmin*ATR1m
    TRIGGER at close of bar i: pullback exists AND close[i] > high[i-1]   (micro higher-high resumption)
    ENTRY at open[i+1], STOP = min(pullback_low, low[i]) - 1 tick
    INVALIDATION: pullback depth > retr_max * impulse size  -> disarm (that is no longer a shallow continuation pullback)
  One entry per arm. Shorts mirrored.
HTF bars are aligned to the session grid (bar start ET); a HTF bar is known only after its last 1-min bar closed,
so arming starts at the NEXT 1-min bar.
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from prep import load, TICK

def base():
    df = load()
    return df

def htf(df, tf):
    """HTF bars from 1m (all sessions). returns frame with last 1m index, ohlc, atr"""
    k = df.smin.values // tf
    g = df.assign(k=k, i=np.arange(len(df))).groupby(['sess', 'k'], sort=False)
    b = g.agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'),
              first=('i', 'first'), last=('i', 'last'), n=('i', 'size')).reset_index()
    b['smin_end'] = (b.k + 1) * tf
    pc = b.close.shift(1); tr = np.maximum(b.high, pc) - np.minimum(b.low, pc)
    b['atr'] = tr.rolling(20, min_periods=20).mean()
    b['sid'] = pd.factorize(b.sess)[0]
    b['same_prev'] = b.sid.values == np.r_[-1, b.sid.values[:-1]]
    return b

def tod_of_smin(sm): return (18 * 60 + sm) % 1440

def entry_machine(df, arms, dmin=0.5, retr_max=0.6, expiry=45, win=None, min_pb_bars=1):
    """arms: DataFrame with a (first 1m idx usable), d, imp_hi, imp_lo, imp_size, exp (last idx allowed for trigger)"""
    o, h, l, c, atr, tod = (df[k].values for k in ('open', 'high', 'low', 'close', 'atr20', 'tod'))
    sess = pd.factorize(df.sess)[0]
    n = len(df); out = []
    for a, d, ihi, ilo, isz, ex in zip(arms.a.values, arms.d.values, arms.imp_hi.values, arms.imp_lo.values,
                                       arms.imp_size.values, arms.exp.values):
        if d > 0:
            run = ihi; pbl = np.inf; nb = 0
            for i in range(a, min(ex, n - 2) + 1):
                if sess[i] != sess[a]: break
                if nb >= min_pb_bars and (run - pbl) >= dmin * atr[i - 1] and c[i] > h[i - 1]:
                    stop = min(pbl, l[i]) - TICK
                    out.append((i, 1, stop, run - pbl, a)); break
                if h[i] > run:
                    run = h[i]; pbl = np.inf; nb = 0
                else:
                    pbl = min(pbl, l[i]); nb += 1
                    if run - pbl > retr_max * isz: break
        else:
            run = ilo; pbh = -np.inf; nb = 0
            for i in range(a, min(ex, n - 2) + 1):
                if sess[i] != sess[a]: break
                if nb >= min_pb_bars and (pbh - run) >= dmin * atr[i - 1] and c[i] < l[i - 1]:
                    stop = max(pbh, h[i]) + TICK
                    out.append((i, -1, stop, pbh - run, a)); break
                if l[i] < run:
                    run = l[i]; pbh = -np.inf; nb = 0
                else:
                    pbh = max(pbh, h[i]); nb += 1
                    if pbh - run > retr_max * isz: break
    E = pd.DataFrame(out, columns=['sig', 'd', 'stop', 'pb_depth', 'arm'])
    E['e'] = E.sig + 1
    E['entry'] = o[E.e.values]
    E['R'] = (E.entry - E.stop) * E.d
    E = E[sess[E.e.values] == sess[E.sig.values]]      # (R>0 is enforced after the stop floor, see candidates.py)
    E['etod'] = tod[E.e.values]
    if win is not None:
        E = E[(E.etod >= win[0]) & (E.etod < win[1])]
    return E.reset_index(drop=True)

def arms_htf_impulse(df, tf, nbars=3, k=1.5, tod_from=None, tod_to=None, cluster=None, expiry=45):
    """Arm when a HTF bar closes with nbars-move >= k*ATR_htf. cluster=(minutes) -> require a previous same-direction
    HTF impulse whose close is within `cluster` minutes before this one (impulse cluster / 'staircase')."""
    b = htf(df, tf)
    ok = b.same_prev.values
    c = b.close.values; atr = b.atr.values; s = b.sid.values
    mv = np.full(len(b), np.nan)
    same_n = s == np.r_[[-1] * nbars, s[:-nbars]]
    mv[nbars:] = c[nbars:] - c[:-nbars]
    mv[~same_n] = np.nan
    d = np.where(mv >= k * atr, 1, np.where(mv <= -k * atr, -1, 0))
    b['d'] = d; b['mv'] = mv
    end_tod = tod_of_smin(b.smin_end.values)
    b['end_tod'] = end_tod
    sel = (d != 0) & (b.n.values >= tf - 1)
    if tod_from is not None: sel &= (end_tod >= tod_from) & (end_tod <= tod_to)
    if cluster:
        prev_ok = np.zeros(len(b), bool)
        idx = np.flatnonzero(d != 0)
        for j in np.flatnonzero(sel):
            look = cluster // tf
            for q in range(max(0, j - look), j):
                if d[q] == d[j] and s[q] == s[j]: prev_ok[j] = True; break
        sel &= prev_ok
    B = b[sel]
    # impulse extremes over the nbars HTF bars
    hi = b.high.rolling(nbars).max().values[sel]; lo = b.low.rolling(nbars).min().values[sel]
    A = pd.DataFrame({'a': B['last'].values + 1, 'd': B.d.values, 'imp_hi': hi, 'imp_lo': lo,
                      'imp_size': np.abs(B.mv.values), 'atr_htf': B.atr.values})
    A['exp'] = A.a + expiry - 1
    return A

def arms_compression(df, tf=5, look=6, comp=2.5, brk_k=1.0, tod_from=None, tod_to=None, expiry=30):
    """Compression -> expansion: range of previous `look` HTF bars <= comp*ATR_htf, then a HTF bar closes beyond
    that range with its own range >= brk_k*ATR_htf. Arms pullback entry in breakout direction."""
    b = htf(df, tf)
    hi = b.high.rolling(look).max().shift(1).values; lo = b.low.rolling(look).min().shift(1).values
    s = b.sid.values; same = s == np.r_[[-1] * (look + 1), s[:-(look + 1)]]
    rng = hi - lo; atr = b.atr.values
    compressed = (rng <= comp * atr) & same
    bar_rng = (b.high - b.low).values
    up = compressed & (b.close.values > hi) & (bar_rng >= brk_k * atr)
    dn = compressed & (b.close.values < lo) & (bar_rng >= brk_k * atr)
    d = np.where(up, 1, np.where(dn, -1, 0))
    end_tod = tod_of_smin(b.smin_end.values)
    sel = (d != 0)
    if tod_from is not None: sel &= (end_tod >= tod_from) & (end_tod <= tod_to)
    B = b[sel]
    A = pd.DataFrame({'a': B['last'].values + 1, 'd': d[sel],
                      'imp_hi': np.maximum(B.high.values, hi[sel]), 'imp_lo': np.minimum(B.low.values, lo[sel]),
                      'imp_size': (np.where(d[sel] > 0, B.high.values - lo[sel], hi[sel] - B.low.values)),
                      'atr_htf': atr[sel]})
    A['exp'] = A.a + expiry - 1
    return A

def arms_random(df, tf, tod_from, tod_to, per_day, k=1.5, expiry=45, seed=0):
    """CONTROL: arms at random 1m bars inside the window, random direction; impulse box = last tf*3 minutes."""
    rng = np.random.default_rng(seed)
    b = htf(df, tf)
    atr_map = pd.Series(b.atr.values, index=b['last'].values).reindex(np.arange(len(df))).ffill().values
    good = df.good.values; tod = df.tod.values
    cand = np.flatnonzero(good & (tod >= tod_from) & (tod <= tod_to))
    nd = df.sess[good].nunique()
    pick = np.sort(rng.choice(cand, int(per_day * nd), replace=False))
    L = tf * 3
    hi = df.high.rolling(L).max().values; lo = df.low.rolling(L).min().values
    A = pd.DataFrame({'a': pick, 'd': rng.choice([-1, 1], len(pick)), 'imp_hi': hi[pick - 1], 'imp_lo': lo[pick - 1],
                      'imp_size': k * atr_map[pick - 1], 'atr_htf': atr_map[pick - 1]})
    A['exp'] = A.a + expiry - 1
    return A.dropna()
