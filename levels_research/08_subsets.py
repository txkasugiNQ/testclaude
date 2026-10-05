"""OBSERVATION 3: which level constellations differ from placebo? TRAIN only, split into two halves
(2023 / 2024H1) to see whether a difference is stable. Metric: E@0.5R and E@1R (conservative)."""
import pandas as pd, numpy as np, sys
from engine import *
tag = sys.argv[1] if len(sys.argv) > 1 else "1m_v2"
E = pd.read_pickle(f"es_{tag}_train.pkl")
b = pd.read_pickle(f"bars_{tag}.pkl")
E = E[E.risk.notna() & (E.risk >= 4)].copy()
E["half"] = np.where(pd.to_datetime(b.tday.values[E.bar.values]) < pd.Timestamp("2024-01-01"), "H23", "H24")
m = E["mod"]
E["sess"] = pd.cut((m - 1080) % 1440, [-1, 540, 840, 930, 1020, 1200, 1320, 1440],
                   labels=["Asia18-03", "LDN03-08", "Pre08-0930", "NYopen-11", "NYmid11-14", "NYpm14-16", "late16-18"])
k = E.kind.fillna(0).astype(int)
E["src"] = np.select([E.pool == 1, E.pool == 2, k & 4 > 0, k & 2 > 0, (k & 1 > 0) & (k & 8 > 0), k & 1 > 0, k & 8 > 0],
                     ["key", "placebo", "range", "major", "swing+HTF", "swing", "HTF-only"], "other")
mm = E.mtfmask.fillna(0).astype(int)
E["htf"] = np.select([mm & 48 > 0, mm & 8 > 0, mm & 2 > 0, mm & 1 > 0], ["4H/D", "1H", "15m", "5m"], "none")
E["ntest"] = E.touches.clip(upper=3).astype(int).astype(str).replace({"3": "3+"})
E["age_h"] = pd.cut((E.bar - E.created) / 60, [-1, 1, 4, 24, 1e9], labels=["<1h", "1-4h", "4-24h", ">24h"])
E["clu"] = pd.cut(E.n_s05, [-1, 0, 1, 3, 1e9], labels=["0", "1", "2-3", "4+"])
E["keyconf"] = pd.cut(E.n_k05, [-1, 0, 1e9], labels=["noKey", "key<=0.5ATR"])
E["strength_b"] = pd.cut(E.strength, [-1, 3, 5, 7, 1e9], labels=["weak", "mod", "strong", "HC"])
E["keyname"] = E.keytype.map(lambda v: KEYNAMES[int(v)] if v == v and v >= 0 else "")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
def summ(g):
    r = {"n": len(g)}
    for kk in ["0.5", "1.0"]:
        r[f"E{kk}"] = g[f"R{kk}"].mean()
    for hh in ["H23", "H24"]:
        r[f"E1_{hh}"] = g.loc[g.half == hh, "R1.0"].mean()
    r["WR.5"] = (g["R0.5"] > 0).mean()
    return pd.Series(r)
out = []
for et in [EV_TOUCH, EV_REJECT, EV_SWEEP, EV_BREAK, EV_FAKE, EV_RETEST]:
    S = E[E.etype == et]
    print(f"\n################ {ETNAMES[et]}  (placebo E1={S[S.pool==2]['R1.0'].mean():.3f}, E0.5={S[S.pool==2]['R0.5'].mean():.3f})")
    for feat in ["src", "htf", "ntest", "age_h", "clu", "keyconf", "strength_b", "sess"]:
        sub = S if feat in ["src", "sess", "ntest", "clu", "keyconf"] else S[S.pool == 0]
        if feat in ["sess", "ntest", "clu", "keyconf"]:
            g = sub.groupby([feat, sub.pool.map({0: "IND", 1: "KEY", 2: "PLAC"})], observed=True).apply(summ)
        else:
            g = sub.groupby(feat, observed=True).apply(summ)
        g = g[g.n >= 300]
        print(f"--- {feat}\n", g.round(3).to_string())
    K = S[S.pool == 1]
    print("--- key type\n", K.groupby("keyname").apply(summ).query("n>=100").round(3).to_string())
