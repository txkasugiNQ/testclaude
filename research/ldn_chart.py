import sys, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ldn_lab import *
lb = LB(2); L = lb.L
def plot_day(d, fn):
    sel = (lb.tdate == d) & (lb.ltod > 300) & (lb.ltod <= 780)
    idx = np.where(sel)[0]; x = lb.ltod[idx]
    fig, ax = plt.subplots(figsize=(22, 9))
    for i, xx in zip(idx, x):
        col = '#26a69a' if lb.c[i] >= lb.o[i] else '#ef5350'
        ax.vlines(xx, lb.l[i], lb.h[i], color=col, lw=0.8)
        ax.add_patch(plt.Rectangle((xx - 0.7, min(lb.o[i], lb.c[i])), 1.4, max(abs(lb.c[i] - lb.o[i]), 0.25), color=col))
    j = idx[-1]
    for k, col, ls in (('asiah','purple','--'),('asial','purple','--'),('frah','orange',':'),('fral','orange',':'),('pdh','blue',':'),('pdl','blue',':'),('pdc','gray',':'),('gx_open','black','-.')):
        v = L[k][j]
        if np.isfinite(v): ax.axhline(v, color=col, ls=ls, lw=0.9); ax.text(305, v, k, color=col, fontsize=8, va='bottom', clip_on=True)
    for k, col in (('or30h','green'),('or30l','red')):
        v = L[k][j]; ax.hlines(v, 510, 720, color=col, lw=1)
    ax.axvspan(480, 720, color='yellow', alpha=0.06); ax.axvspan(480, 510, color='green', alpha=0.05)
    ax.set_xticks(range(300, 781, 30)); ax.set_xticklabels([f'{m//60:02d}:{m%60:02d}' for m in range(300, 781, 30)])
    lo, hi = lb.l[idx].min(), lb.h[idx].max(); pad = (hi - lo) * 0.05; ax.set_ylim(lo - pad, hi + pad); ax.grid(alpha=0.2)
    lsel = idx[(x > 480) & (x <= 720)]
    ax.set_title(f'{d} {pd.Timestamp(d).day_name()}  London (2m, London time)  London range={lb.h[lsel].max()-lb.l[lsel].min():.0f}  Asia range={L["asiah"][j]-L["asial"][j]:.0f}  ATR2m={lb.atr[lsel].mean():.1f}')
    fig.tight_layout(); fig.savefig(fn, dpi=60); plt.close(fig)
rng = np.random.default_rng(int(sys.argv[1]))
days = [d for d in lb.udays if str(d) <= '2024-06-30']
for d in sorted(rng.choice(days, int(sys.argv[2]), replace=False)):
    plot_day(d, f'ldn_charts/{d}.png'); print(d)
