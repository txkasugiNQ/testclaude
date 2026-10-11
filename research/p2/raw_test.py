"""Raw edge of setups: fixed brackets, no management. Compared with the identical entry machine armed at random times."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from signals import *
from engine import excursions, outcomes

df = base()
good = df.good.values
A = {k: df[k].values for k in ('high', 'low', 'close', 'open')}; A['sess'] = pd.factorize(df.sess)[0]
atr1 = df.atr20.values
def T(h, m): return h * 60 + m

def evaluate(E, H=90):
    E = E[good[E.e.values]].copy()
    fav, adv, valid, cl = excursions(A, E.e.values, E.d.values, E.entry.values, E.R.values, H=H, with_close=True)
    out = outcomes(fav, adv, valid, cl)
    for k in ('ev_0.5', 'ev_1.0', 'ev_2.0', 'win_0.5', 'win_1.0', 'win_2.0', 'mfe_pre_stop', 'mae_pre_1R'):
        E[k] = out[k]
    E['t1'] = out['t_1.0']
    E['yr'] = pd.DatetimeIndex(df.sess.values[E.e.values]).year
    E['R_atr'] = E.R / atr1[E.sig.values]
    return E

def summary(E, name):
    nd = df[good].groupby(df.sess[good].dt.year).sess.nunique()
    r = {'setup': name, 'n': len(E), 'n/day': len(E) / nd.sum(), 'R_pts_med': E.R.median(), 'R_atr1_med': E.R_atr.median()}
    for k in ('ev_0.5', 'ev_1.0', 'ev_2.0'): r[k] = E[k].mean()
    r['win_1.0'] = E['win_1.0'].mean()
    for y in (2023, 2024, 2025):
        r[f'ev1_{y}'] = E[E.yr == y]['ev_1.0'].mean(); r[f'ev2_{y}'] = E[E.yr == y]['ev_2.0'].mean()
    r['ev1_long'] = E[E.d > 0]['ev_1.0'].mean(); r['ev1_short'] = E[E.d < 0]['ev_1.0'].mean()
    return r

if __name__ == '__main__':
    rows = []; store = {}
    MID = (T(12, 0), T(14, 30)); AM = (T(9, 45), T(12, 15))
    setups = {
        'H1 MID 15m-IMP -> 1m PB': (arms_htf_impulse(df, 15, 3, 1.5, T(12, 0), T(14, 15), expiry=45), MID, 15),
        'H1b MID 15m-IMP(2bar,1.2) -> 1m PB': (arms_htf_impulse(df, 15, 2, 1.2, T(12, 0), T(14, 15), expiry=45), MID, 15),
        'H1c AM 15m-IMP -> 1m PB': (arms_htf_impulse(df, 15, 3, 1.5, T(9, 45), T(12, 0), expiry=45), AM, 15),
        'H2 AM 5m-IMP cluster -> 1m PB': (arms_htf_impulse(df, 5, 3, 1.5, T(9, 45), T(12, 0), cluster=30, expiry=20), AM, 5),
        'H2b AM 5m-IMP any -> 1m PB': (arms_htf_impulse(df, 5, 3, 1.5, T(9, 45), T(12, 0), expiry=20), AM, 5),
        'H2c MID 5m-IMP cluster -> 1m PB': (arms_htf_impulse(df, 5, 3, 1.5, T(12, 0), T(14, 15), cluster=30, expiry=20), MID, 5),
        'H3 MID 5m compression->breakout -> 1m PB': (arms_compression(df, 5, 6, 2.5, 1.0, T(12, 0), T(14, 15), expiry=30), MID, 5),
        'H3b AM 5m compression->breakout -> 1m PB': (arms_compression(df, 5, 6, 2.5, 1.0, T(9, 45), T(12, 0), expiry=30), AM, 5),
    }
    for name, (arms, win, tf) in setups.items():
        E = evaluate(entry_machine(df, arms, win=win, expiry=None))
        rows.append(summary(E, name)); store[name] = E
        per_day = max(len(arms) / 730, 1.0)
        C = pd.concat([evaluate(entry_machine(df, arms_random(df, tf, win[0], win[1] - 15, per_day, seed=s), win=win))
                       for s in range(3)])
        rows.append(summary(C, '   control (random arms) ' + name.split()[0])); store['CTRL ' + name] = C
        print(name, 'arms', len(arms), 'entries', len(E), flush=True)
    R = pd.DataFrame(rows)
    pd.to_pickle(store, os.path.join(os.path.dirname(__file__), '..', 'output', 'p2_raw.pkl'))
    pd.set_option('display.width', 300, 'display.max_columns', 40)
    print(R.round(3).to_string(index=False))
