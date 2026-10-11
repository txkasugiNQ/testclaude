"""Phase 3 step 2: time-based entries -> trades with trailing (same verified simulator as Phase 2).
Entry rule for a slot (T, anchor): at the CLOSE of the bar that ends at T (bar start T-1) compute
  move = close - anchor_price;  d = sign(move);  optional |move| >= mmin * DR
Entry = open of bar starting at T. Initial stop = signal close - d * k * DR (rounded to tick away).
DR = mean RTH range of the previous 10 sessions (causal).
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'p2'))
from sim import simulate, params
from prep import load, TICK
_ctx = {}
def ctx():
    if _ctx: return _ctx
    df = load()
    df['sid'] = pd.factorize(df.sess)[0]
    g = df[df.good]
    rth = g[(g.tod >= 570) & (g.tod < 960)].groupby('sess').agg(h=('high', 'max'), l=('low', 'min'))
    allsess = pd.Index(df.sess.unique())
    rng = (rth.h - rth.l).reindex(allsess)
    DR = rng.shift(1).rolling(10, min_periods=5).mean()    # previous sessions (NaN for bad days are skipped by rolling)
    df['DR'] = df.sess.map(DR)
    df['rth_open'] = df.open.where(df.tod == 570).groupby(df.sess).ffill()
    idx = pd.Series(np.arange(len(df)), index=pd.MultiIndex.from_arrays([df.sess.values, df.tod.values]))
    _ctx.update(df=df, idx=idx, ARR=tuple(df[k].values.astype(np.float64) for k in ('open', 'high', 'low', 'close', 'atr20')) +
                (df.sid.values.astype(np.int64), df.tod.values.astype(np.float64)), YR=pd.DatetimeIndex(df.sess.values).year.values)
    return _ctx

def slot_entries(T, anchor, k=0.1, mmin=0.0):
    c = ctx(); df = c['df']
    sel = df.good.values & (df.tod.values == T)
    e = np.flatnonzero(sel); s = e - 1
    ok = df.sid.values[s] == df.sid.values[e]; e, s = e[ok], s[ok]
    cl = df.close.values[s]
    if anchor == 'RTH': ap = df.rth_open.values[s]
    elif anchor.startswith('L'):
        L = int(anchor[1:]); j = s - L; ap = np.where(df.sid.values[j] == df.sid.values[s], df.close.values[j], np.nan)
    elif anchor == 'GLX':
        ap = df.open.groupby(df.sess).transform('first').values[s]
    mv = cl - ap; DR = df.DR.values[s]
    d = np.sign(mv)
    keep = np.isfinite(mv) & np.isfinite(DR) & (d != 0) & (np.abs(mv) >= mmin * DR)
    e, s, d, cl, DR, mv = e[keep], s[keep], d[keep].astype(np.int64), cl[keep], DR[keep], mv[keep]
    stop = cl - d * k * DR
    stop = np.where(d > 0, np.floor(stop / TICK) * TICK, np.ceil(stop / TICK) * TICK)
    return pd.DataFrame({'e': e, 'sig': s, 'd': d, 'stop': stop, 'DR': DR, 'mv_dr': mv / DR, 'T': T})

def run(E, P, cost_pts=0.6):
    c = ctx()
    E = E.sort_values('e', kind='mergesort').reset_index(drop=True)
    r = simulate(*c['ARR'], E.e.values.astype(np.int64), E.d.values.astype(np.int64), E.stop.values.astype(np.float64), P)
    T = E.copy()
    T['taken'] = r[:, 0] == 1; T['xi'] = r[:, 1]; T['pnl'] = r[:, 2]; T['Rpts'] = r[:, 3]; T['mfe'] = r[:, 4]; T['mae'] = r[:, 5]
    T['bars'] = r[:, 6]; T['reason'] = r[:, 7]
    T = T[T.taken].copy()
    T['pnl_net'] = T.pnl - cost_pts / T.Rpts
    T['sess'] = c['df'].sess.values[T.e.values]; T['yr'] = c['YR'][T.e.values]
    return T
