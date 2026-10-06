"""Phase H: does continuation live at a coarser scale? Same generic triggers on 3/5/15-min bars.
Bars built per session from bar-start ET minutes (aligned to smin grid). Entry next bar open, 1-ATR(20, same TF) stop,
first-passage evaluated on the SAME timeframe bars (tie -> stop). Control = all bars both directions.
"""
import numpy as np, pandas as pd, sys
from prep import load
from engine import excursions, outcomes
df = load(); df = df[df.good]
def resample(tf):
    g = df.assign(k=df.smin // tf).groupby(['sess', 'k'])
    b = g.agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'), smin=('smin', 'first')).reset_index()
    b['smin'] = b.k * tf
    pc = b.close.shift(1); tr = np.maximum(b.high, pc) - np.minimum(b.low, pc)
    b['atr'] = tr.rolling(20).mean()
    return b
def lbl(sm): t = (18*60+sm) % 1440; return f'{t//60:02d}:{t%60:02d}'
CANDS = [('18:00', 90), ('22:00', 150), ('01:00', 210), ('05:00', 120), ('07:00', 150), ('09:30', 90), ('11:00', 90), ('12:30', 120), ('14:30', 90)]
def sm(h): a, b_ = map(int, h.split(':')); return (a*60+b_-18*60) % 1440
out = []
for tf in (1, 3, 5, 15):
    b = resample(tf); n = len(b)
    o, h, l, c, atr = (b[k].values for k in ('open', 'high', 'low', 'close', 'atr'))
    ss = b.sess.values.astype('datetime64[D]').astype(np.int64)
    def lag(a, k):
        r = np.full(n, np.nan); r[k:] = a[:-k]; m = np.zeros(n, bool); m[k:] = ss[k:] == ss[:-k]; r[~m] = np.nan; return r
    mv = c - lag(c, 3)   # 3-bar impulse
    imp = np.where(mv >= 1.5 * atr, 1, np.where(mv <= -1.5 * atr, -1, 0))
    mv10 = c - lag(c, 10)
    pb = np.where((lag(c, 1) < lag(o, 1)) & (c > lag(h, 1)) & (mv10 >= 1.5 * atr), 1,
                  np.where((lag(c, 1) > lag(o, 1)) & (c < lag(l, 1)) & (mv10 <= -1.5 * atr), -1, 0))
    A = {'high': h, 'low': l, 'sess': ss}
    def run(t, d):
        e = t + 1; ok = (e < n); ok[ok] &= ss[np.minimum(e, n-1)][ok] == ss[t[ok]]; ok &= ~np.isnan(atr[t])
        t, d, e = t[ok], d[ok], e[ok]
        fav, adv, valid = excursions(A, e, d, o[e], atr[t], H=max(10, 60 // tf))
        r = outcomes(fav, adv, valid)
        return pd.DataFrame({'sm': b.smin.values[e], 'yr': pd.DatetimeIndex(b.sess.values[t]).year,
                             'w0.5': r['win_0.5'], 'w1': r['win_1.0'], 'w2': r['win_2.0']})
    tabs = {}
    for name, s in (('IMP', imp), ('PB', pb)):
        t = np.flatnonzero(s); tabs[name] = run(t, s[t])
    allt = np.arange(n - 1)
    tabs['CTRL'] = pd.concat([run(allt, np.ones(len(allt), int)), run(allt, -np.ones(len(allt), int))])
    for st, L in CANDS:
        s0 = sm(st)
        sel = {k: v[(v.sm >= s0) & (v.sm < s0 + L)] for k, v in tabs.items()}
        for trig in ('IMP', 'PB'):
            r = {'tf': tf, 'window': f'{st}+{L}', 'trig': trig, 'n/day': len(sel[trig]) / 730}
            for k in ('w0.5', 'w1', 'w2'):
                r[f'edge_{k}'] = sel[trig][k].mean() - sel['CTRL'][k].mean()
            for y in (2023, 2024, 2025):
                r[f'e1_{y}'] = sel[trig][sel[trig].yr == y]['w1'].mean() - sel['CTRL'][sel['CTRL'].yr == y]['w1'].mean()
            r['ctrl_w1'] = sel['CTRL']['w1'].mean()
            out.append(r)
    print('done tf', tf, flush=True)
O = pd.DataFrame(out); O.to_csv('output/H_scale.csv', index=False)
pd.set_option('display.width', 250, 'display.max_rows', 200)
print(O.round(3).to_string(index=False))
