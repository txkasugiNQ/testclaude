"""OBSERVATION 5: what typically happens after price reaches a level? (TRAIN only)
Classification of the 15 bars after a touch (incl. the touch bar), all in ATR units, reaction dir = d:
  pen   = max penetration beyond the level (through side)
  after = (close[t+15] - level) * d
  CLEAN_REJECT : pen <= 0.25 and after >= 1
  SWEEP_RECLAIM: pen >  0.25 and after >= 0.5
  BREAK_GO     : after <= -1
  CHOP         : everything else
Also: level beyond the developing day extreme (touch = new day high/low) vs inside the day range."""
import pandas as pd, numpy as np
from engine import *
b = pd.read_pickle("bars_1m_v2.pkl"); ev = pd.read_pickle("events_1m_v2.pkl")
h, l, c = b.high.values, b.low.values, b.close.values
T = ev[(ev.split == "train") & (ev.etype == EV_TOUCH)].copy()
t = T.bar.values; d = T.edir.values; L = T.price.values; A = T.atr.values
N = 15
ok = t + N < len(c)
T = T[ok]; t = t[ok]; d = d[ok]; L = L[ok]; A = A[ok]
idx = t[:, None] + np.arange(0, N + 1)[None, :]
pen = np.where(d == 1, (L - l[idx].min(1)), (h[idx].max(1) - L)) / A
after = (c[t + N] - L) * d / A
T["pen"] = pen; T["after"] = after
T["beh"] = np.select([(pen <= 0.25) & (after >= 1), (pen > 0.25) & (after >= 0.5), after <= -1],
                     ["CLEAN_REJECT", "SWEEP_RECLAIM", "BREAK_GO"], "CHOP")
# developing day extremes BEFORE the touch bar
g = b.groupby("day")
dh = g.high.cummax().shift(1).values.copy(); dl = g.low.cummin().shift(1).values.copy()
first = np.r_[True, b.day.values[1:] != b.day.values[:-1]]
dh[first] = np.nan; dl[first] = np.nan
T["outside"] = np.where(d == -1, L > dh[t], L < dl[t])   # resistance above day high / support below day low
k = T.kind.fillna(0).astype(int); mm = T.mtfmask.fillna(0).astype(int)
T["cls"] = np.select([T.pool == 2, T.pool == 1, mm & 56 > 0, k & 2 > 0, k & 1 > 0], ["PLACEBO", "KEY", "HTF>=1H", "MAJOR", "SWING"], "other")
T["first"] = np.where(T.touches == 0, "1st", "later")
pd.set_option("display.width", 250)
tab = pd.crosstab([T.cls, T["first"]], T.beh, normalize="index").round(3)
tab["n"] = T.groupby(["cls", "first"]).size()
print("Behaviour after a touch (shares)\n", tab.to_string())
tab2 = pd.crosstab([T.cls, T.outside], T.beh, normalize="index").round(3)
tab2["n"] = T.groupby(["cls", "outside"]).size()
print("\nLevel OUTSIDE the developing day range (True) vs inside\n", tab2.to_string())
S = T[T.pool == 0]
tab3 = pd.crosstab(S.eqhits.fillna(0).clip(upper=1).map({0: "no EQ", 1: "equal H/L"}), S.beh, normalize="index").round(3)
print("\nEqual highs/lows (indicator eqHits)\n", tab3.to_string(), "\n", S.eqhits.fillna(0).clip(upper=1).value_counts().to_dict())
T[["bar", "pool", "cls", "first", "beh", "pen", "after", "outside"]].to_pickle("behaviour_train.pkl")
