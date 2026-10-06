"""Phase D: coarse-scale continuation.
1) Variance ratio per window & year: VR(k)=Var(sum of k 1-min returns)/(k*Var(1-min)), returns normalised by day's RTH-independent ATR.
   VR>1 -> trending/persistent at that scale, VR<1 -> mean-reverting.
2) 'Move already started' test: at time t (every 15 min), past return over L min predicts next H min? Pooled across days per year.
"""
import numpy as np, pandas as pd
from prep import load
df = load(); df = df[df.good]
df['yr'] = df.sess.dt.year
# 1-min log-ish returns normalised by causal atr20
c = df.close.values; same = np.r_[False, df.sess.values[1:] == df.sess.values[:-1]]
r = np.r_[np.nan, np.diff(c)] / df.atr20.shift(1).values
r[~same] = np.nan
df['r'] = r
# minute grid matrix per session: rows=sessions, cols=smin
piv = df.pivot_table(index='sess', columns='smin', values='close')
atrp = df.pivot_table(index='sess', columns='smin', values='atr20')
yrs = pd.DatetimeIndex(piv.index).year.values
P = piv.values; AT = atrp.values
def lbl(sm): t = (18*60+sm) % 1440; return f'{t//60:02d}:{t%60:02d}'

# --- VR per window (block of 60 min), k=5 and 15 ---
rows = []
for s in range(0, 1380-61+1, 30):
    for yr in (2023, 2024, 2025):
        m = yrs == yr
        seg = P[m][:, s:s+61]; a = AT[m][:, s][:, None]
        d1 = np.diff(seg, axis=1) / a
        out = {'start': lbl(s), 'yr': yr}
        for k in (5, 15, 30):
            dk = (seg[:, k::k][:, :60//k] - seg[:, 0:60:k][:, :60//k]) / a
            out[f'VR{k}'] = np.nanvar(dk) / (k * np.nanvar(d1))
        rows.append(out)
V = pd.DataFrame(rows).pivot(index='start', columns='yr')
V = V.reindex([lbl(s) for s in range(0, 1380-61+1, 30)])
pd.set_option('display.width', 250, 'display.max_rows', 300)
print('Variance ratio of 60-min windows (VR>1 trending). columns: VR5/VR15/VR30 x year')
print(V.round(2).to_string())
V.to_csv('output/D_vr.csv')

# --- past L -> next H continuation beta at 15-min grid, per year ---
rows = []
for s in range(60, 1380-30, 15):
    for L in (15, 30, 60):
        for H in (15, 30, 60):
            if s - L < 0 or s + H > 1379: continue
            for yr in (2023, 2024, 2025):
                m = yrs == yr
                a = AT[m][:, s]
                x = (P[m][:, s] - P[m][:, s-L]) / a; y = (P[m][:, s+H] - P[m][:, s]) / a
                ok = ~np.isnan(x) & ~np.isnan(y)
                x, y = x[ok], y[ok]
                rows.append({'t': lbl(s), 'L': L, 'H': H, 'yr': yr, 'corr': np.corrcoef(x, y)[0, 1],
                             'hit': (np.sign(x) == np.sign(y)).mean()})
M = pd.DataFrame(rows)
M.to_pickle('output/D_mom.pkl')
Mp = M.pivot_table(index=['t'], columns=['L', 'H', 'yr'], values='corr')
# summarise: average corr over (L,H) and min over years
summ = M.groupby(['t', 'yr'])['corr'].mean().unstack()
summ['mean'] = summ.mean(1); summ['min'] = summ[[2023, 2024, 2025]].min(1)
summ = summ.reindex([lbl(s) for s in range(60, 1380-30, 15)])
print('\nPast-move -> next-move correlation (avg over L,H in {15,30,60}); per year')
print(summ.round(3).to_string())
