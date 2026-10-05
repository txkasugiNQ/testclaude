"""OBSERVATION 2: raw event study (TRAIN only). For every indicator event a 'natural' trade:
  TOUCH / REJECT / SWEEP -> trade the reaction (away from level); stop beyond the bar's extreme past the level
  BREAK                  -> trade continuation; stop on the other side of the level
  FAKE                   -> trade back inside; stop beyond the false-break extreme
  RETEST                 -> trade the breakout direction; stop beyond the level
Entry next bar open, conservative intrabar, fixed targets 0.25..2R, flat 15:55 or after H bars.
Compared against identical events on PLACEBO levels."""
import pandas as pd, numpy as np, sys
from engine import *
from outcomes import fixed_r
tag = sys.argv[1] if len(sys.argv) > 1 else "1m_v2"
b = pd.read_pickle(f"bars_{tag}.pkl"); ev = pd.read_pickle(f"events_{tag}.pkl")
o, h, l, c = b.open.values, b.high.values, b.low.values, b.close.values
day = b.day.values; mod = b["mod"].values
tfm = int(tag.split("m")[0])
H = max(240 // tfm, 40)
E = ev[(ev.split == "train") & ev.etype.between(1, 6)].copy()
E["atr"] = b.atr.values[E.bar.values]
buf = np.maximum(0.15 * E.atr.values, TICK) + TICK
d = E.edir.values; t = E.bar.values
# extreme of the event bar beyond the level
barext = np.where(d == 1, l[t], h[t])
lvl_edge = np.where(d == 1, E.bot.values, E.top.values)
stop = np.full(len(E), np.nan)
et = E.etype.values
# reaction types: stop beyond min(bar extreme, level edge) on the adverse side
reac = np.isin(et, [EV_TOUCH, EV_REJECT, EV_SWEEP])
stop[reac] = np.where(d[reac] == 1, np.minimum(barext[reac], lvl_edge[reac]) - buf[reac],
                      np.maximum(barext[reac], lvl_edge[reac]) + buf[reac])
# break: other side of the level (+buffer)
br = et == EV_BREAK
stop[br] = np.where(d[br] == 1, E.bot.values[br] - buf[br], E.top.values[br] + buf[br])
# fake: beyond the false-break extreme (x2 holds the extreme price of the fake bar; use max with level)
fk = et == EV_FAKE
ext = E.x2.values
stop[fk] = np.where(d[fk] == 1, np.minimum(ext[fk], E.bot.values[fk]) - buf[fk], np.maximum(ext[fk], E.top.values[fk]) + buf[fk])
# retest: beyond retest bar extreme / level
rt = et == EV_RETEST
stop[rt] = np.where(d[rt] == 1, np.minimum(l[t[rt]], E.bot.values[rt]) - buf[rt], np.maximum(h[t[rt]], E.top.values[rt]) + buf[rt])
ks = np.array([0.25, 0.33, 0.5, 0.67, 0.75, 1.0, 1.5, 2.0])
R, risk, mfe, mae, tb = fixed_r(o, h, l, c, day, t, d.astype(np.int64), stop, ks, H, 1315, (mod - 1080) % 1440)
for q, k in enumerate(ks):
    E[f"R{k}"] = R[:, q]
E["risk"] = risk; E["mfeR"] = mfe; E["maeR"] = mae; E["risk_atr"] = risk / E.atr
E["mod"] = mod[t]
E.to_pickle(f"es_{tag}_train.pkl")
E = E[E.risk.notna()]
E["grp"] = E.pool.map({0: "IND", 1: "KEY", 2: "PLAC"})
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
def summ(g):
    out = {"n": len(g), "riskpts": g.risk.median()}
    for k in [0.25, 0.5, 0.75, 1.0, 2.0]:
        out[f"E@{k}"] = g[f"R{k}"].mean()
    out["WR@0.5"] = (g["R0.5"] > 0).mean()
    out["MFEmed"] = g.mfeR.median()
    return pd.Series(out)
print("tag", tag, "train events with valid risk:", len(E))
print(E.groupby(["etype", "grp"]).apply(summ).rename(index=ETNAMES, level=0).round(3))
# realistic min risk (>= 4 pts) only
F = E[E.risk >= 4]
print("\n--- only risk >= 4 pts")
print(F.groupby(["etype", "grp"]).apply(summ).rename(index=ETNAMES, level=0).round(3))
