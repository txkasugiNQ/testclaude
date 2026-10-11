"""Phase E: fine grid over the day (5-min starts) for a pure micro-momentum continuation map.
Entry direction = sign(close_t - close_{t-5}) when |move| >= q * atr (q in {0,1,2}); entry next open.
Stop: 1 ATR (fixed, same for control) -> first-passage edge vs. random-direction control at same minutes.
Plus VR5/VR15 per (start,len) per year. Results saved for plotting.
"""
import numpy as np, pandas as pd
from prep import load
df = load()
T = pd.read_pickle('output/B_events.pkl')
C = T[(T.trig == 'CTRL') & (T.stop == 'atr1')].copy()
c = df.close.values; atr = df.atr20.values; sess = df.sess.values
mv5 = np.full(len(df), np.nan); mv5[5:] = c[5:] - c[:-5]
bad = np.ones(len(df), bool); bad[5:] = sess[5:] != sess[:-5]; mv5[bad] = np.nan
C['mv'] = mv5[C.t.values] / atr[C.t.values]
C['agree'] = np.sign(C.mv) == C.d          # this control entry is in direction of last 5-min move
C['sm'] = (C.etod - 18 * 60) % 1440
for a in (0.25, 0.5, 1.0): C[f'w{a}'] = C[f'win_{a}'].astype(float)
C['fe30'] = C.mfe30 - C.mae30
# per minute & year & bin sums -> fast window aggregation
C['bin'] = np.select([C.mv.abs() >= 2, C.mv.abs() >= 1, C.mv.abs() >= 0], [2, 1, 0], -1)
G = C.groupby(['yr', 'sm', 'bin', 'agree'])[['w0.25', 'w0.5', 'w1.0', 'fe30']].agg(['sum', 'count'])
G.to_pickle('output/E_minute_sums.pkl')
print(C.groupby(['bin', 'agree'])[['w0.25', 'w0.5', 'w1.0', 'fe30']].mean().round(4))
print(C.groupby(['yr', 'bin', 'agree'])[['w0.5', 'fe30']].mean().unstack().round(4))
