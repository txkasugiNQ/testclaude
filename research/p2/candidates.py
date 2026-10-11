"""Builds the candidate entry list for the main setup (no look-ahead), with a configurable stop rule."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from signals import base, arms_compression, arms_htf_impulse, entry_machine, TICK
def T(h, m): return h * 60 + m
_df = None
def get_df():
    global _df
    if _df is None:
        _df = base()
        _df['rth_open'] = _df.open.where(_df.tod == 570).groupby(_df.sess).ffill()  # causal: NaN before 09:30
        _df['sid'] = pd.factorize(_df.sess)[0]
    return _df

def setup_entries(name='H3', win=(T(12, 0), T(14, 30)), arm_to=T(14, 15), comp=2.5, look=6, brk_k=1.0, expiry=30,
                  dmin=0.5, retr_max=0.6, day_filter=True, stop_floor_atr=0.0, mode='pb'):
    df = get_df()
    if name == 'H3':
        arms = arms_compression(df, 5, look, comp, brk_k, win[0], arm_to, expiry=expiry)
    elif name == 'H2':
        arms = arms_htf_impulse(df, 5, 3, 1.5, win[0], arm_to, cluster=30, expiry=20)
    elif name == 'H1':
        arms = arms_htf_impulse(df, 15, 3, 1.5, win[0], arm_to, expiry=45)
    if mode == 'pb':
        E = entry_machine(df, arms, dmin=dmin, retr_max=retr_max, win=win)
    else:
        E = pd.DataFrame({'sig': arms.a.values - 1, 'd': arms.d.values}); E['e'] = E.sig + 1
        E['entry'] = df.open.values[E.e.values]; E['etod'] = df.tod.values[E.e.values]
        E = E[(E.etod >= win[0]) & (E.etod < win[1])].copy()
        E['stop'] = np.nan   # immediate mode: stop = floor only
    s = E.sig.values
    if day_filter:
        c = df.close.values; ro = df.rth_open.values
        E = E[np.sign(c[s] - ro[s]) == E.d.values]
    s = E.sig.values
    atr = df.atr20.values
    # floor referenced to the signal-bar CLOSE (known when the order is sent; Pine-compatible)
    floor = df.close.values[s] - E.d.values * stop_floor_atr * atr[s]
    if stop_floor_atr > 0:
        # stop must be at least stop_floor_atr*ATR1m away: take the farther of structure and floor
        E['stop'] = np.where(np.isnan(E.stop.values), floor, np.where(E.d.values > 0, np.minimum(E.stop.values, floor), np.maximum(E.stop.values, floor)))
    # tick-round stop away from entry
    E['stop'] = np.where(E.d.values > 0, np.floor(E.stop / TICK) * TICK, np.ceil(E.stop / TICK) * TICK)
    E['R'] = (E.entry - E.stop) * E.d
    E = E[df.good.values[E.e.values] & (E.R > 0)]
    return E.sort_values('e', kind='mergesort').reset_index(drop=True)
