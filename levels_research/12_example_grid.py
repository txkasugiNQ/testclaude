"""Random (not cherry-picked) first-touch examples, TRAIN only: key levels vs placebo, with behaviour label."""
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
b = pd.read_pickle("bars_1m_v2.pkl"); B = pd.read_pickle("behaviour_train.pkl")
ev = pd.read_pickle("events_1m_v2.pkl")
o, h, l, c = b.open.values, b.high.values, b.low.values, b.close.values
for cls, seed in [("KEY", 1), ("HTF>=1H", 2), ("PLACEBO", 3)]:
    S = B[(B.cls == cls) & (B["first"] == "1st")].sample(16, random_state=seed).sort_values("bar")
    fig, axs = plt.subplots(4, 4, figsize=(20, 14))
    for ax, (_, r) in zip(axs.ravel(), S.iterrows()):
        t = int(r.bar); lv = ev.loc[(ev.bar == t) & (ev.etype == 1) & (ev.pool == r.pool)]
        e = ev.loc[_]
        a, z = t - 30, t + 31
        x = np.arange(a, z) - t
        up = c[a:z] >= o[a:z]
        ax.vlines(x, l[a:z], h[a:z], color=np.where(up, "#26a69a", "#ef5350"), lw=0.8)
        ax.bar(x, np.abs(c[a:z] - o[a:z]).clip(0.25), bottom=np.minimum(o[a:z], c[a:z]), color=np.where(up, "#26a69a", "#ef5350"), width=0.7)
        ax.axhline(e.price, color="#2962ff", lw=1.2, ls="--"); ax.axvline(0, color="k", lw=0.5, alpha=0.4)
        ax.axvspan(0, 15, color="#ffd54f", alpha=0.12)
        name = "" if np.isnan(e.keytype) else ["PDH","PDL","PDC","PWH","PWL","ONH","ONL","LDNH","LDNL","pRTHH","pRTHL","ORH","ORL"][int(e.keytype)]
        ax.set_title(f"{b.t.iloc[t]:%Y-%m-%d %H:%M} {name} {'res' if e.edir == -1 else 'sup'} -> {r.beh}", fontsize=9)
        ax.tick_params(labelsize=7)
    fig.suptitle(f"16 RANDOM first touches - {cls} (1m, TRAIN). yellow = 15-bar classification window", fontsize=12)
    fig.tight_layout(); fig.savefig(f"examples_firsttouch_{cls.replace('>=','ge').replace('/','')}.png", dpi=65); plt.close(fig)
print("ok")
