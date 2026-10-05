"""OBSERVATION 4: first test of significant levels, barrier race from the level at several scales.
TRAIN only. +1 = price moved X away in the reaction direction before moving X through the level."""
import pandas as pd, numpy as np
from engine import *
from outcomes import first_passage
b = pd.read_pickle("bars_1m_v2.pkl"); ev = pd.read_pickle("events_1m_v2.pkl")
h, l, c = b.high.values, b.low.values, b.close.values; day = b.day.values
T = ev[(ev.split == "train") & (ev.etype == EV_TOUCH) & (ev.touches == 0)].copy()
k = T.kind.fillna(0).astype(int); mm = T.mtfmask.fillna(0).astype(int)
T["cls"] = np.select([T.pool == 1, T.pool == 2, mm & 56 > 0, k & 2 > 0, mm & 2 > 0, k & 1 > 0],
                     ["KEY", "PLACEBO", "HTF 1H/4H/D", "MAJOR", "HTF 15m", "SWING"], "other")
T["keyname"] = T.keytype.map(lambda v: KEYNAMES[int(v)] if v == v and v >= 0 else "")
T.loc[T.pool == 1, "cls"] = "KEY " + T.loc[T.pool == 1, "keyname"].map(
    lambda s: "PD/PW" if s in ["PDH", "PDL", "PWH", "PWL", "PDC"] else ("ON/LDN" if s in ["ONH", "ONL", "LDNH", "LDNL"] else "RTH/OR"))
T["held"] = (c[T.bar.values] - T.price.values) * T.edir.values > 0
H = 390
for X in [5, 10, 20, 30]:
    r, _ = first_passage(h, l, c, day, T.bar.values, T.price.values, T.edir.values.astype(np.int64),
                         np.full(len(T), float(X)), H, False)
    T[f"x{X}"] = r
def summ(g):
    o = {"n": len(g)}
    for X in [5, 10, 20, 30]:
        r = g[f"x{X}"]; d = r.isin([1, -1]); p = (r[d] == 1).mean()
        o[f"P{X}"] = p; o[f"se{X}"] = np.sqrt(p * (1 - p) / max(d.sum(), 1))
    return pd.Series(o)
pd.set_option("display.width", 250)
print("FIRST TOUCH, all"); print(T.groupby("cls").apply(summ).round(3).to_string())
print("\nFIRST TOUCH, held at close"); print(T[T.held].groupby("cls").apply(summ).round(3).to_string())

# ---- control for close distance from level, and stability across train halves
T["cd"] = (c[T.bar.values] - T.price.values) * T.edir.values / T.atr.values
T["cdb"] = pd.cut(T.cd, [-99, -1, -0.25, 0, 0.5, 1, 2, 99])
T["half"] = np.where(pd.to_datetime(b.tday.values[T.bar.values]) < pd.Timestamp("2024-01-01"), "H23", "H24")
T["grp3"] = np.select([T.cls.str.startswith("KEY ON") | T.cls.str.startswith("KEY RTH"), T.cls == "HTF 1H/4H/D",
                       T.cls.str.startswith("KEY PD"), T.cls == "PLACEBO", T.cls.isin(["SWING", "MAJOR"])],
                      ["KEY session", "HTF>=1H", "KEY PD/PW", "PLACEBO", "SWING/MAJOR"], "x")
def p10(g):
    r = g["x10"]; d = r.isin([1, -1]); return pd.Series({"n": d.sum(), "P10": (r[d] == 1).mean()})
print("\nP(react 10pts first) by close-distance bucket (ATR) and group")
print(T[T.grp3 != "x"].groupby(["cdb", "grp3"], observed=True).apply(p10).unstack().round(3).to_string())
print("\nheld, by half")
print(T[T.held & (T.grp3 != "x")].groupby(["grp3", "half"]).apply(p10).unstack().round(3).to_string())
T.to_pickle("firsttouch_train.pkl")
