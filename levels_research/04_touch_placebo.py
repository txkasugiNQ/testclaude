"""OBSERVATION 1: do price reactions at indicator levels differ from reactions at placebo prices?
TRAIN split only."""
import pandas as pd, numpy as np, sys
from engine import *
from outcomes import first_passage
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 1
b = pd.read_pickle(f"bars_{tf}m.pkl"); ev = pd.read_pickle(f"events_{tf}m.pkl")
h, l, c = b.high.values, b.low.values, b.close.values; day = b.day.values
t = ev[(ev.split == "train") & (ev.etype == EV_TOUCH)].copy()
t["cl"] = c[t.bar.values]
t["held"] = (t.cl - t.price) * t.edir > 0
H = 120 // tf if tf > 1 else 120
for m in [1, 2, 4]:
    r, tt = first_passage(h, l, c, day, t.bar.values, t.price.values, t.edir.values.astype(np.int64),
                          m * t.atr.values, H, False)
    t[f"r{m}"] = r
def summ(g):
    out = {"n": len(g)}
    for m in [1, 2, 4]:
        r = g[f"r{m}"]; dec = r.isin([1, -1])
        out[f"P(react){m}A"] = (r[dec] == 1).mean()
        out[f"amb{m}"] = (r == 0).mean()
    return pd.Series(out)
t["iso"] = (t.d_s > 0.5 * t.atr) & (t.d_k > 0.5 * t.atr)
t["grp"] = t.pool.map({0: "indicator", 1: "key", 2: "placebo"})
pd.set_option("display.width", 200)
for held in [None, True]:
    s = t if held is None else t[t.held]
    print("\n==== touches", "ALL" if held is None else "HELD AT CLOSE (close back on approach side)")
    print(s.groupby(["grp", "iso"]).apply(summ).round(3))
s = t[t.held]
print("\n==== indicator levels, held, by #other structural levels within 0.5 ATR")
print(s[s.pool == 0].groupby(s.n_s05.clip(upper=5)).apply(summ).round(3))
print("\n==== placebo, held, by #structural levels within 0.5 ATR")
print(s[s.pool == 2].groupby(s.n_s05.clip(upper=5)).apply(summ).round(3))
print("\n==== key levels (held) by type")
k = s[s.pool == 1]
print(k.groupby(k.keytype.astype(int).map(dict(enumerate(KEYNAMES)))).apply(summ).round(3))
t.to_pickle(f"touch_{tf}m_train.pkl")
