"""How much directional drift follows each setup (stop-independent), and how does bracket EV depend on stop size?
Drift_h = mean( (close[e+h-1] - entry) * d ) in points and in ATR1m units (h minutes after entry, same session)."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from signals import *
from engine import excursions, outcomes
df = base(); good = df.good.values
A = {k: df[k].values for k in ('high', 'low', 'close', 'open')}; A['sess'] = pd.factorize(df.sess)[0]
c = df.close.values; atr1 = df.atr20.values; sid = A['sess']; n = len(df)
def T(h, m): return h * 60 + m
MID = (T(12, 0), T(14, 30)); AM = (T(9, 45), T(12, 15))

def immediate(arms, win):
    """entry at the first bar after the arm (HTF close) - Phase-1 style"""
    E = pd.DataFrame({'sig': arms.a.values - 1, 'd': arms.d.values}); E['e'] = E.sig + 1
    E['entry'] = df.open.values[E.e.values]; E['etod'] = df.tod.values[E.e.values]
    return E[(E.etod >= win[0]) & (E.etod < win[1])].reset_index(drop=True)

def drift(E):
    E = E[good[E.e.values]]
    r = {'n/day': len(E) / 730}
    yr = pd.DatetimeIndex(df.sess.values[E.e.values]).year
    for h in (5, 15, 30, 60):
        j = np.minimum(E.e.values + h - 1, n - 1)
        ok = sid[j] == sid[E.e.values]
        v = (c[j] - E.entry.values) * E.d.values
        r[f'drift{h}_pts'] = v[ok].mean(); r[f'drift{h}_atr'] = (v / atr1[E.sig.values])[ok].mean()
        if h == 30:
            for y in (2023, 2024, 2025): r[f'd30_{y}'] = (v / atr1[E.sig.values])[ok & (yr == y)].mean()
            r['d30_tstat'] = (v / atr1[E.sig.values])[ok].mean() / ((v / atr1[E.sig.values])[ok].std() / np.sqrt(ok.sum()))
    return r

def stop_scan(E, mults=(1, 1.5, 2, 3, 4, 6)):
    E = E[good[E.e.values]]
    r = {}
    for m in mults:
        R = m * atr1[E.sig.values]
        fav, adv, valid, cl = excursions(A, E.e.values, E.d.values, E.entry.values, R, H=120, with_close=True)
        o = outcomes(fav, adv, valid, cl)
        r[f'm{m}_ev1'] = o['ev_1.0'].mean(); r[f'm{m}_ev2'] = o['ev_2.0'].mean()
    return r

setups = {
 'H1 MID 15m-IMP': (arms_htf_impulse(df, 15, 3, 1.5, T(12, 0), T(14, 15), expiry=45), MID, 15),
 'H1c AM 15m-IMP': (arms_htf_impulse(df, 15, 3, 1.5, T(9, 45), T(12, 0), expiry=45), AM, 15),
 'H2 AM 5m-IMP cluster': (arms_htf_impulse(df, 5, 3, 1.5, T(9, 45), T(12, 0), cluster=30, expiry=20), AM, 5),
 'H2c MID 5m-IMP cluster': (arms_htf_impulse(df, 5, 3, 1.5, T(12, 0), T(14, 15), cluster=30, expiry=20), MID, 5),
 'H3 MID 5m comp->brk': (arms_compression(df, 5, 6, 2.5, 1.0, T(12, 0), T(14, 15), expiry=30), MID, 5),
 'H3b AM 5m comp->brk': (arms_compression(df, 5, 6, 2.5, 1.0, T(9, 45), T(12, 0), expiry=30), AM, 5),
}
rows = []
for name, (arms, win, tf) in setups.items():
    for mode in ('immediate', 'pullback'):
        E = immediate(arms, win) if mode == 'immediate' else entry_machine(df, arms, win=win)
        r = {'setup': name, 'entry': mode, **drift(E), **stop_scan(E)}; rows.append(r)
    Cr = arms_random(df, tf, win[0], win[1] - 15, max(len(arms) / 730, 1), seed=1)
    for mode in ('immediate', 'pullback'):
        E = immediate(Cr, win) if mode == 'immediate' else entry_machine(df, Cr, win=win)
        rows.append({'setup': 'CTRL ' + name, 'entry': mode, **drift(E), **stop_scan(E)})
    print(name, flush=True)
R = pd.DataFrame(rows); R.to_csv('../output/p2_drift.csv', index=False)
pd.set_option('display.width', 400, 'display.max_columns', 60)
print(R[['setup', 'entry', 'n/day', 'drift5_pts', 'drift15_pts', 'drift30_pts', 'drift60_pts', 'drift30_atr', 'd30_2023', 'd30_2024', 'd30_2025', 'd30_tstat']].round(3).to_string(index=False))
print(R[['setup', 'entry'] + [c for c in R.columns if c.startswith('m')]].round(3).to_string(index=False))
