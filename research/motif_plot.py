import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
km,M,R=pd.read_pickle('motifs.pkl')
cent=km.cluster_centers_
fig,axs=plt.subplots(1,3,figsize=(13,3.6))
for ax,cl in zip(axs,(2,9,27)):
    shp=cent[cl][:24]; ax.plot(range(-23,1),shp,color='#1f4e79',lw=2)
    r=R[R.cl==cl].iloc[0]
    ax.axhline(0,color='#999',lw=0.6); ax.set_title(f"cluster {cl}: fwd30m {r.m2023:+.1f}/{r.m2024:+.1f}/{r.m2025:+.1f} %ATR (23/24/25)",fontsize=8)
    ax.set_xlabel('5-min bars (0 = now)',fontsize=7); ax.tick_params(labelsize=7); ax.grid(color='#e0e0e0',lw=0.4)
    ax.text(0.02,0.95,f"range {cent[cl][24]/2:.2f} ATR\nhigh@{cent[cl][25]:.2f} low@{cent[cl][26]:.2f}",transform=ax.transAxes,fontsize=7,va='top')
fig.tight_layout(); fig.savefig('charts/motif_centroids.png',dpi=110)
for cl in (2,9,27):
    g=M[M.cl==cl]; tod=pd.cut(g['mod'],[575,630,690,780,870,961],labels=['09:35-10:30','10:30-11:30','11:30-13:00','13:00-14:30','14:30-16:00'])
    print(f"cluster {cl}: n={len(g)}  time-of-day share:",(tod.value_counts(normalize=True).sort_index().round(2)).to_dict(), " mean 2h range %.2f ATR"%g.rng.mean())
