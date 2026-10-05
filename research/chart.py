import pandas as pd, numpy as np, sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from core import *
df = pd.read_pickle('nq2.pkl'); t = pd.read_pickle('days.pkl')

def resample(x, tf):
    # x: 1m bars with tod (close label). bucket so that bars align to session minutes: bucket = ceil(tod/tf)*tf
    b = ((x.tod - 1)//tf + 1)*tf
    g = x.groupby(b)
    return pd.DataFrame(dict(open=g.open.first(), high=g.high.max(), low=g.low.min(), close=g.close.last(), vol=g.volume.sum(), vwap=g.vwap_rth.last()))

def candles(ax, r, xs, w):
    up = r.close >= r.open
    for (i, row), x, u in zip(r.iterrows(), xs, up):
        col = '#26a69a' if u else '#ef5350'
        ax.vlines(x, row.low, row.high, color=col, lw=0.7)
        ax.add_patch(plt.Rectangle((x-w/2, min(row.open,row.close)), w, max(abs(row.close-row.open), 0.25), color=col))

def plot_day(td, tf=2, start=9*60+30, end=16*60, fn=None):
    x = df[(df.tdate==td)&(df.tod>start)&(df.tod<=end)]
    r = resample(x, tf)
    fig, ax = plt.subplots(figsize=(22,9))
    xs = r.index.values
    candles(ax, r, xs, tf*0.7)
    ax.plot(xs, r.vwap, color='orange', lw=1, label='RTH VWAP')
    L = t.loc[td]
    for k,c,ls in [('onh','purple','--'),('onl','purple','--'),('pdh','blue',':'),('pdl','blue',':'),('pdc','gray',':'),('amh','green','-'),('aml','red','-'),('rth_open','black','-.')]:
        v = L.get(k)
        if pd.notna(v):
            ax.axhline(v, color=c, ls=ls, lw=0.9); ax.text(xs[0], v, k, color=c, fontsize=8, va='bottom', clip_on=True)
    ax.axvspan(12*60, 16*60, color='yellow', alpha=0.06)
    for h in range(10,17): ax.axvline(h*60, color='k', lw=0.3)
    ax.set_xticks(range(start - start%30, end+1, 30)); ax.set_xticklabels([f'{m//60}:{m%60:02d}' for m in range(start-start%30, end+1, 30)])
    lo, hi = r.low.min(), r.high.max(); pad=(hi-lo)*0.05
    ax.set_ylim(lo-pad, hi+pad); ax.grid(alpha=0.2)
    rng = L.amh-L.aml
    ax.set_title(f'{td} {pd.Timestamp(td).day_name()} tf={tf}m  AMrange={rng:.0f} PMrange={L.pmh-L.pml:.0f}  ONrange={L.onh-L.onl:.0f}')
    fig.tight_layout(); fig.savefig(fn or f'charts/{td}_{tf}m.png', dpi=60); plt.close(fig)

if __name__ == '__main__':
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv)>1 else 0)
    days = t[(t.n_pm==240)&(t.index<=IS_END)].index.values
    pick = rng.choice(days, int(sys.argv[2]) if len(sys.argv)>2 else 12, replace=False)
    for d in sorted(pick):
        plot_day(d, tf=int(sys.argv[3]) if len(sys.argv)>3 else 2); print(d)
