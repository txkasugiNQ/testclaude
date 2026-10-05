"""CHART step: random TRAIN windows, candles + levels exactly as known at each bar (line starts at the
bar where the level ENTERED the database, ends where it was removed) + key levels + events."""
import pandas as pd, numpy as np, sys, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from engine import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 1
NW = int(sys.argv[2]) if len(sys.argv) > 2 else 60
W = 180 if tf == 1 else 160
os.makedirs(f"charts_{tf}m", exist_ok=True)
b = pd.read_pickle(f"bars_{tf}m.pkl"); ev = pd.read_pickle(f"events_{tf}m.pkl")
cr = ev[(ev.pool == 0) & (ev.etype == EV_CREATE)][["uid", "bar", "price"]]
rm = ev[(ev.pool == 0) & (ev.etype == EV_REMOVE)][["uid", "bar"]].rename(columns={"bar": "rbar"})
LV = cr.merge(rm, on="uid", how="left").fillna({"rbar": len(b)})
kinds = ev[(ev.pool == 0) & (ev.etype.isin([EV_CREATE, EV_MERGE]))].groupby("uid").kind.max()
LV["kind"] = LV.uid.map(kinds).fillna(0).astype(int)
inter = ev[(ev.pool.isin([0, 1])) & (ev.etype.between(1, 6))]
rng = np.random.default_rng(42)
cand = b.index[(b.split == "train") & (b["mod"].between(180, 960 - W * tf))].values
starts = np.sort(rng.choice(cand, NW, replace=False))
col = {1: "#888888", 2: "#d62728", 4: "#9467bd", 8: "#1f77b4"}
mk = {EV_TOUCH: ("o", "#999999", 10), EV_REJECT: ("D", "#2ca02c", 18), EV_SWEEP: ("X", "#ff7f0e", 40),
      EV_BREAK: ("^", "#1f77b4", 22), EV_FAKE: ("x", "#d62728", 40), EV_RETEST: ("s", "#17becf", 22)}
for wi, s0 in enumerate(starts):
    s1 = s0 + W
    w = b.iloc[s0:s1]
    if w.tday.nunique() > 1:
        s1 = s0 + (w.tday == w.tday.iloc[0]).sum(); w = b.iloc[s0:s1]
    x = np.arange(len(w))
    lo, hi = w.low.min(), w.high.max(); pad = (hi - lo) * 0.08
    fig, ax = plt.subplots(figsize=(15, 7.5))
    up = w.close >= w.open
    ax.vlines(x, w.low, w.high, color=np.where(up, "#26a69a", "#ef5350"), lw=0.8)
    ax.bar(x, (w.close - w.open).abs().clip(lower=0.25), bottom=np.minimum(w.open, w.close),
           color=np.where(up, "#26a69a", "#ef5350"), width=0.7)
    alive = LV[(LV.bar < s1) & (LV.rbar > s0) & LV.price.between(lo - pad, hi + pad)]
    for _, r in alive.iterrows():
        a = max(r.bar - s0 + 1, 0); z = min(r.rbar - s0, len(w) - 1)   # usable from bar AFTER creation
        k = int(r.kind)
        c_ = col[2] if k & 2 else col[4] if k & 4 else col[8] if (k & 8 and not k & 1) else col[1]
        ax.hlines(r.price, a, z, color=c_, lw=1.4 if k & 2 else 0.8, alpha=0.8)
    for kt, name in enumerate(KEYNAMES):
        v = w[name].values
        ok = ~np.isnan(v) & (v > lo - pad) & (v < hi + pad)
        if ok.any():
            ax.plot(np.where(ok, x, np.nan), np.where(ok, v, np.nan), ls="--", color="#2962ff", lw=1.0)
            j = np.where(ok)[0][-1]; ax.text(j + 0.5, v[j], name, color="#2962ff", fontsize=7, va="center")
    e = inter[(inter.bar >= s0) & (inter.bar < s1)]
    for et, (m, cc, sz) in mk.items():
        ee = e[e.etype == et]
        if len(ee):
            ax.scatter(ee.bar - s0, ee.price, marker=m, color=cc, s=sz, zorder=5, label=ETNAMES[et])
    ax.set_ylim(lo - pad, hi + pad); ax.set_xlim(-1, len(w) + 8)
    ticks = x[::max(len(w) // 12, 1)]
    ax.set_xticks(ticks); ax.set_xticklabels(w.t.dt.strftime("%H:%M").values[ticks], fontsize=8)
    ax.set_title(f"#{wi} {w.t.iloc[0]:%Y-%m-%d %a} {tf}m  ATR={w.atr.iloc[0]:.1f}  levels in view={len(alive)}  "
                 f"(grey=swing red=major purple=range blue=HTF-only, dashed=key)", fontsize=10)
    ax.legend(loc="upper left", fontsize=7, ncol=6); ax.grid(alpha=0.15)
    fig.tight_layout(); fig.savefig(f"charts_{tf}m/w{wi:02d}.png", dpi=80); plt.close(fig)
print("done", len(starts))
