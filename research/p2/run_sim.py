import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sim import simulate, params
from candidates import get_df, setup_entries
df = get_df()
ARR = tuple(df[k].values.astype(np.float64) for k in ('open', 'high', 'low', 'close', 'atr20')) + \
      (df.sid.values.astype(np.int64), df.tod.values.astype(np.float64))
YR = pd.DatetimeIndex(df.sess.values).year.values

def run(E, P, cost_pts=0.0):
    r = simulate(*ARR, E.e.values.astype(np.int64), E.d.values.astype(np.int64), E.stop.values.astype(np.float64), P)
    T = E.copy()
    T['taken'] = r[:, 0] == 1; T['xi'] = r[:, 1]; T['pnl'] = r[:, 2]; T['Rpts'] = r[:, 3]; T['mfe'] = r[:, 4]
    T['mae'] = r[:, 5]; T['bars'] = r[:, 6]; T['reason'] = r[:, 7]
    T = T[T.taken].copy()
    T['pnl_net'] = T.pnl - cost_pts / T.Rpts
    T['sess'] = df.sess.values[T.e.values]; T['yr'] = YR[T.e.values]
    return T

def metrics(T, col='pnl', ndays=None):
    if ndays is None: ndays = 730
    x = T[col].values
    eps = 1e-9
    win = x > eps; loss = x < -eps
    r = {'trades': len(x), 'tr/day': len(x) / ndays, 'WR': win.mean(), 'BE%': (~win & ~loss).mean(), 'LR': loss.mean(),
         'avgW': x[win].mean() if win.any() else 0, 'avgL': x[loss].mean() if loss.any() else 0, 'exp': x.mean(),
         'PF': x[win].sum() / -x[loss].sum() if loss.any() else np.inf}
    eq = np.cumsum(x); r['maxDD'] = (np.maximum.accumulate(eq) - eq).max()
    s = 0; ms = 0
    for v in x:
        s = s + 1 if v < -eps else 0; ms = max(ms, s)
    r['maxLstreak'] = ms
    return r
