"""Render random examples (winners vs losers) for a range/deviation close-continuation setup. 2023 only."""
import sys, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from rangelib import *
build_all()
name=sys.argv[1]; k=float(sys.argv[2]); tag=sys.argv[3]; YEARS=[int(x) for x in (sys.argv[4] if len(sys.argv)>4 else "2023").split(",")]
R=RANGES[name].astype(np.float64)
ev=np.array(close_events(h,l,c,R,k,0,10)); t=ev[:,0].astype(np.int64); d=ev[:,1]; W=ev[:,2]; lv=ev[:,3]
ok=np.isin(YR[t],YEARS)&~np.isnan(A[t]); t,d,W,lv=t[ok],d[ok],W[ok],lv[ok]
res=sym_from_close(o,h,l,c,t,d,0.1*A[t],flat)
# map each event back to its range (H,L, formation start/end) for drawing
Rmap={}
for r in R:
    Rmap[(int(r[3]))]=r
def find_range(tt):
    best=None
    for r in R:
        if r[3]<=tt<=r[4]: best=r
    return best
UP,DN='#26a69a','#ef5350'
def panel(ax,tt,dd,ww,lvl,out):
    rr=find_range(tt); H,L=rr[0],rr[1]
    a=max(int(rr[2])-60,tt-150); b=min(tt+120,flat[tt])
    seg=df.iloc[a:b+1]; b5=seg.set_index('ts')[['o','h','l','c']].resample('3min',label='right',closed='right').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    for x,(o_,h_,l_,c_) in enumerate(b5.values):
        col=UP if c_>=o_ else DN; ax.plot([x,x],[l_,h_],color=col,lw=0.6); ax.add_patch(Rectangle((x-0.35,min(o_,c_)),0.7,max(abs(c_-o_),0.25),color=col,lw=0))
    ax.axhspan(L,H,color='#1f4e79',alpha=0.08); ax.axhline(H,color='#1f4e79',lw=0.6); ax.axhline(L,color='#1f4e79',lw=0.6)
    for kk,ls in ((0.5,'--'),(1.0,':'),(1.5,':')):
        ax.axhline(H+kk*(H-L),color='#777',lw=0.6,ls=ls); ax.axhline(L-kk*(H-L),color='#777',lw=0.6,ls=ls)
    xe=np.searchsorted(b5.index.values,df.ts.values[tt]); ax.axvline(xe,color='k',lw=0.6)
    ax.plot([xe],[c[tt]],marker='^' if dd>0 else 'v',color='k',ms=7)
    s=0.1*A[tt]; ax.axhline(c[tt]+dd*s,color=UP,lw=0.8,ls='-.'); ax.axhline(c[tt]-dd*s,color=DN,lw=0.8,ls='-.')
    ax.set_ylim(min(seg.l.min(),L-0.6*(H-L)),max(seg.h.max(),H+0.6*(H-L)))
    ax.set_title(f"{pd.Timestamp(df.ts.values[tt]).strftime('%Y-%m-%d %H:%M')} {'LONG' if dd>0 else 'SHORT'}  W={ww:.0f}  {'WIN' if out>0 else 'LOSS'}",fontsize=7)
    ticks=[i for i,ts_ in enumerate(b5.index) if ts_.minute==0]; ax.set_xticks(ticks); ax.set_xticklabels([b5.index[i].strftime('%H') for i in ticks],fontsize=6); ax.tick_params(axis='y',labelsize=6)
rng=np.random.default_rng(3)
for lab,mask in (('win',res>0),('loss',res<0)):
    idx=rng.choice(np.where(mask)[0],8,replace=False)
    fig,axs=plt.subplots(2,4,figsize=(17,7.5))
    for ax,j in zip(axs.flat,idx): panel(ax,t[j],d[j],W[j],lv[j],res[j])
    fig.suptitle(f"{name}  close beyond {k}x range  -> continuation  ({lab}s, random {YEARS})  | box=range, dashed=0.5x, dotted=1x/1.5x, dash-dot=+-0.1ATR barriers",fontsize=9)
    fig.tight_layout(); fig.savefig(f'charts/rd_{tag}_{lab}.png',dpi=100); plt.close(fig)
print("events 2023:",len(t),"win share",np.mean(res[res!=0]>0).round(3))
