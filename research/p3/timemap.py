"""Phase 3 step 1: time-based continuation map.
For each session, entry time T (bar START, ET), anchor A and horizon H:
  move  = price at T (close of bar T-1)  - anchor price          (known before entry)
  d     = sign(move)                                               (continuation)
  fwd   = close of bar T+H-1 - open of bar T                       (entry at T open, exit after H minutes)
  y     = d * fwd / DR, DR = mean RTH (09:30-16:00) range of the 10 PREVIOUS sessions (causal vol unit)
Anchors: PREV = previous session 15:59 bar close (prior RTH close), GLX = 18:00 session open, RTH = 09:30 open,
         and rolling lookbacks L15/L30/L60/L120.
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from prep import load
df = load(); df = df[df.good]
C = df.pivot_table(index='sess', columns='smin', values='close')
O = df.pivot_table(index='sess', columns='smin', values='open')
H_ = df.pivot_table(index='sess', columns='smin', values='high'); L_ = df.pivot_table(index='sess', columns='smin', values='low')
C = C.reindex(columns=range(1380)); O = O.reindex(columns=range(1380))
def sm(tod): return (tod - 1080) % 1440
def tod(smin): return (smin + 1080) % 1440
rth = [sm(t) for t in range(570, 960)]
rng = H_[rth].max(1) - L_[rth].min(1)
DR = rng.shift(1).rolling(10, min_periods=5).mean()          # previous sessions only
prev_close = C[sm(959)].shift(1)                              # previous session 15:59 bar close
yrs = pd.DatetimeIndex(C.index).year.values
Cv, Ov, DRv = C.values, O.values, DR.values
rows = []
Ts = list(range(sm(18 * 60 + 30), sm(9 * 60 + 30), 15)) + list(range(sm(9 * 60 + 35), sm(15 * 60 + 50), 5))
for T in Ts:
    t_et = tod(T)
    pT = Cv[:, T - 1]; oT = Ov[:, T]
    anchors = {'PREV': prev_close.values, 'GLX': Ov[:, 0]}
    if t_et > 570 and t_et < 1080: anchors['RTH'] = Ov[:, sm(570)]
    for L in (15, 30, 60, 120):
        if T - 1 - L >= 0: anchors[f'L{L}'] = Cv[:, T - 1 - L]
    for an, ap in anchors.items():
        mv = pT - ap; d = np.sign(mv)
        for Hh in (15, 30, 60, 120):
            if T + Hh - 1 > sm(16 * 60 + 59): continue
            fwd = Cv[:, T + Hh - 1] - oT
            y = d * fwd / DRv
            ok = np.isfinite(y) & (d != 0)
            r = {'T': f'{t_et//60:02d}:{t_et%60:02d}', 'sm': T, 'anchor': an, 'H': Hh, 'n': ok.sum(),
                 'mean_bp': 1e4 * np.nanmean(y[ok]) / 100, 't': np.nanmean(y[ok]) / (np.nanstd(y[ok]) / np.sqrt(ok.sum())),
                 'hit': (y[ok] > 0).mean()}
            for yy in (2023, 2024, 2025):
                m = ok & (yrs == yy); r[f'y{yy}'] = 100 * np.nanmean(y[m])
            # strong-move subset: |move| >= 0.15 DR
            s = ok & (np.abs(mv) / DRv >= 0.15)
            r['strong_n'] = s.sum(); r['strong_mean'] = 100 * np.nanmean(y[s]) if s.sum() > 30 else np.nan
            for yy in (2023, 2024, 2025):
                m = s & (yrs == yy); r[f's{yy}'] = 100 * np.nanmean(y[m]) if m.sum() > 10 else np.nan
            rows.append(r)
R = pd.DataFrame(rows)
R['mean'] = R.mean_bp; R['min_y'] = R[['y2023', 'y2024', 'y2025']].min(1); R['smin_y'] = R[['s2023', 's2024', 's2025']].min(1)
R.to_pickle('../output/p3_timemap.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 200)
cols = ['T', 'anchor', 'H', 'n', 'mean', 't', 'hit', 'y2023', 'y2024', 'y2025', 'min_y', 'strong_n', 'strong_mean', 'smin_y']
print('units: % of daily range (DR) per trade.  Top by min-year (all moves):')
print(R.sort_values('min_y', ascending=False)[cols].head(40).round(2).to_string(index=False))
print('Top by min-year (strong moves >=0.15 DR):')
print(R[R.strong_n > 150].sort_values('smin_y', ascending=False)[cols].head(30).round(2).to_string(index=False))
