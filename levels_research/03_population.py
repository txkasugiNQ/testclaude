import pandas as pd, numpy as np
from engine import *
b = pd.read_pickle("bars_1m.pkl"); ev = pd.read_pickle("events_1m.pkl")
tr = ev[ev.split == "train"]
ndays = b.loc[b.split=="train","tday"].nunique()
print("train days", ndays)
cr = tr[tr.etype == EV_CREATE]
kmap = {1:"swing(1m)",2:"major(1m)",3:"range",4:"HTF pivot"}
print("created per day by source:\n", (cr.edir.map(kmap).value_counts()/ndays).round(1))
bits={1:"5m",2:"15m",8:"1H",16:"4H",32:"D"}
print("HTF created per day by TF:\n", (cr[cr.edir==4].x2.astype(int).map(bits).value_counts()/ndays).round(1))
mg = tr[tr.etype == EV_MERGE]
print("merges per day by source:\n", (mg.edir.map(kmap).value_counts()/ndays).round(1))
# lifetimes
rm = ev[ev.etype == EV_REMOVE][["uid","bar"]].rename(columns={"bar":"rbar"})
L = cr[["uid","bar","price"]].merge(rm, on="uid", how="left")
L["life"] = L.rbar - L.bar
print("level lifetime (1m bars):\n", L.life.describe(percentiles=[.1,.25,.5,.75,.9,.99]).round(0))
# state of levels at touch time
t = tr[(tr.etype == EV_TOUCH)]
for pool in [0,1,2]:
    tt = t[t.pool==pool]
    print(f"pool {pool}: touches/day {len(tt)/ndays:.0f}")
t0 = t[t.pool==0]
print("rank at touch (0 weak,1 mod,2 strong,3 HC):\n", t0["rank"].value_counts(normalize=True).sort_index().round(3))
print("touch number distribution (touches before this one):\n", t0.touches.clip(upper=10).value_counts(normalize=True).sort_index().round(3))
print("strength at touch:\n", t0.strength.describe(percentiles=[.25,.5,.75,.9,.99]).round(2))
print("kind combos at touch:\n", t0.kind.astype(int).value_counts(normalize=True).head(10).round(3))
print("ATR 1m by year:\n", b.groupby(b.t.dt.year).atr.median().round(2))
print("mergeTol median pts", (b.atr*0.25).median(), "touchTol", (b.atr*0.125).median())
print("distance to nearest other structural level at touch (ATR):\n", (t0.d_s/t0.atr).describe(percentiles=[.1,.25,.5,.75,.9]).round(2))
print("n other levels within 1 ATR:\n", t0.n_s10.value_counts(normalize=True).sort_index().head(12).round(3))
