"""Random (seeded, not cherry-picked) candlestick samples of candidate windows.
1-min candles, RTH VWAP, 5-min impulse events (3x5m move >= 1.5 ATR5, known at 5m bar close) as triangles."""
import numpy as np, pandas as pd, matplotlib, sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from prep import load
UP, DN, INK2, GRID, SURF = '#1baf7a', '#e34948', '#52514e', '#e4e3df', '#fcfcfb'
df = load(); df = df[df.good]
days = df.sess.unique(); rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
win = sys.argv[1] if len(sys.argv) > 1 else '09:30-12:00'
a, b = win.split('-'); ta = int(a[:2])*60+int(a[3:]); tb = int(b[:2])*60+int(b[3:])
pick = rng.choice(days, 8, replace=False)
fig, axs = plt.subplots(4, 2, figsize=(16, 16), facecolor=SURF)
for ax, d in zip(axs.flat, sorted(pick)):
    s = df[(df.sess == d)]
    w = s[(s.tod >= ta - 30) & (s.tod < tb + 30)].reset_index(drop=True)
    x = np.arange(len(w))
    col = np.where(w.close >= w.open, UP, DN)
    ax.vlines(x, w.low, w.high, color=col, lw=0.7)
    ax.bar(x, (w.close - w.open).abs().clip(lower=0.25), bottom=np.minimum(w.open, w.close), color=col, width=0.7)
    v = w.Vwap_RTH.replace(0, np.nan); ax.plot(x, v, color='#4a3aa7', lw=1.2)
    # 5-min impulse events
    w5 = s.assign(k=s.smin // 5).groupby('k').agg(o=('open', 'first'), h=('high', 'max'), l=('low', 'min'), c=('close', 'last'), tod=('tod', 'last'))
    pc = w5.c.shift(1); tr = np.maximum(w5.h, pc) - np.minimum(w5.l, pc); atr5 = tr.rolling(20).mean()
    mv = w5.c - w5.c.shift(3)
    for k, r in w5[(mv.abs() >= 1.5 * atr5)].iterrows():
        if ta <= r.tod < tb:
            i = np.flatnonzero(w.tod.values == r.tod)
            if len(i):
                up = mv[k] > 0
                ax.scatter(i[0], (w.low[i[0]] - 3) if up else (w.high[i[0]] + 3), marker='^' if up else 'v', color='#2a78d6', s=60, zorder=5)
    ax.axvspan(np.argmax(w.tod.values >= ta), np.argmax(w.tod.values >= tb) if (w.tod.values >= tb).any() else len(w), color='#2a78d6', alpha=0.05)
    lab = np.arange(0, len(x), 30); ax.set_xticks(lab, [f'{t//60:02d}:{t%60:02d}' for t in w.tod.values[lab]])
    ax.set_title(f'{pd.Timestamp(d).date()}  ({win} ET, 1-min, ▲▼ = 5-min-Impuls ≥1.5 ATR5, lila = RTH-VWAP)', loc='left', fontsize=9)
    ax.grid(color=GRID, lw=0.5); ax.set_facecolor(SURF)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
fig.tight_layout(); out = f"output/fig4_candles_{win.replace(':', '').replace('-', '_')}.png"; fig.savefig(out, dpi=95); print(out)
