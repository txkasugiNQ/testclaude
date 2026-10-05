import sys, time, pandas as pd, numpy as np
from engine import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 1
v2 = len(sys.argv) > 2 and sys.argv[2] == "v2"
tag = f"{tf}m" + ("_v2" if v2 else "")
df = pd.read_pickle("data_1m.pkl")
b = make_bars(df, tf)
t0 = time.time()
p = dict(P)
if v2:
    p["maxLevels"] = 3000 - 50
ev, nlev, x = run_engine(b, p, v2=v2, cap=3000 if v2 else CAP, max_events=12_000_000)
print("engine secs", time.time() - t0, "events", len(ev))
b["atr"] = x["atr"]; b["vwap"] = x["vwap"]; b["nlev"] = nlev; b["day"] = x["dayIndex"]
for k, name in enumerate(KEYNAMES): b[name] = x["keys"][:, k]
b["split"] = split_of(b["tday"])
ev["split"] = b["split"].values[ev["bar"].values]
b.to_pickle(f"bars_{tag}.pkl"); ev.to_pickle(f"events_{tag}.pkl")
print(ev.groupby(["pool", "etype"]).size().unstack(0))
print("levels alive per bar:", pd.Series(nlev[nlev>0]).describe())
