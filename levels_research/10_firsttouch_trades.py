"""Translate the first-touch observation into trade metrics (TRAIN ONLY, observation stage).
  REJ : first touch bar closes >= 0.5 ATR back on the approach side -> fade the level.
        stop = touch-bar extreme beyond the level + buffer
  ACC : first touch bar closes >= 0.25 ATR beyond the level -> trade continuation.
        stop = touch-bar extreme on the other side + buffer
Entry next bar open, conservative intrabar, flat 15:55 ET, max 240 bars."""
import pandas as pd, numpy as np
from engine import *
from outcomes import fixed_r
b = pd.read_pickle("bars_1m_v2.pkl")
T = pd.read_pickle("firsttouch_train.pkl")
o, h, l, c = b.open.values, b.high.values, b.low.values, b.close.values
day = b.day.values; mod = b["mod"].values
t = T.bar.values; d = T.edir.values.astype(np.int64)
buf = np.maximum(0.15 * T.atr.values, TICK) + TICK
ks = np.array([0.25, 0.33, 0.5, 0.67, 0.75, 1.0, 1.5, 2.0])
rows = []
for setup in ["REJ", "ACC"]:
    if setup == "REJ":
        m = T.cd >= 0.5; dd = d
        stop = np.where(dd == 1, l[t] - buf, h[t] + buf)
    else:
        m = T.cd <= -0.25; dd = -d
        stop = np.where(dd == 1, l[t] - buf, h[t] + buf)
    R, risk, mfe, mae, tb = fixed_r(o, h, l, c, day, t, dd, stop, ks, 240, 1315, (mod - 1080) % 1440)
    for q, k in enumerate(ks):
        T[f"{setup}_R{k}"] = np.where(m, R[:, q], np.nan)
    T[f"{setup}_risk"] = np.where(m, risk, np.nan)
    T[f"{setup}_mfe"] = np.where(m, mfe, np.nan); T[f"{setup}_mae"] = np.where(m, mae, np.nan)
pd.set_option("display.width", 250)
for setup in ["REJ", "ACC"]:
    S = T[T[f"{setup}_risk"].notna()]
    g = S.groupby("grp3")
    out = pd.DataFrame({"n": g.size(), "risk_pts": g[f"{setup}_risk"].median(),
                        **{f"E@{k}": g[f"{setup}_R{k}"].mean() for k in ks},
                        "WR@0.5": g[f"{setup}_R0.5"].apply(lambda x: (x > 0).mean()),
                        "MFE_med": g[f"{setup}_mfe"].median(), "MAE_med": g[f"{setup}_mae"].median()})
    print(f"\n===== {setup}  (TRAIN)\n", out.round(3).to_string())
    K = S[S.grp3 == "KEY session"]
    print(" by key name (E@0.5, E@1, n):")
    print(K.groupby("keyname").agg(n=("bar", "size"), E05=(f"{setup}_R0.5", "mean"), E1=(f"{setup}_R1.0", "mean")).round(3).to_string())
    print(" by half:")
    print(K.groupby("half").agg(n=("bar", "size"), E05=(f"{setup}_R0.5", "mean"), E1=(f"{setup}_R1.0", "mean")).round(3).to_string())
T.to_pickle("firsttouch_trades_train.pkl")
