"""Render real NQ candle charts for visual scanning (discovery set = 2023 only)."""
import sys, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
df=pd.read_pickle('feats.pkl')
UP,DN,GRID='#26a69a','#ef5350','#d0d0d0'
def candles(ax,bars,w=0.7):
    for k,(o_,h_,l_,c_) in enumerate(bars[['o','h','l','c']].values):
        col=UP if c_>=o_ else DN
        ax.plot([k,k],[l_,h_],color=col,lw=0.6,zorder=2)
        ax.add_patch(Rectangle((k-w/2,min(o_,c_)),w,max(abs(c_-o_),0.25),color=col,lw=0,zorder=3))
    ax.set_xlim(-1,len(bars)); ax.grid(color=GRID,lw=0.4,zorder=0)
def day_chart(ax,sd,tf='5min',start='08:00',end='16:00'):
    g=df[df.sd==sd].set_index('ts')
    seg=g.between_time(start,end)
    b=seg[['o','h','l','c']].resample(tf,label='right',closed='right').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    candles(ax,b)
    x=lambda t: np.searchsorted(b.index.values,np.datetime64(t))
    rth=g.between_time('09:31','16:00')
    lv={'PDH':g.ph.iloc[-1],'PDL':g.pl.iloc[-1]}
    on=g.between_time('00:00','09:30'); ev=g[g.index.hour>=18]; ovn=pd.concat([ev,on])
    lv['ONH']=ovn.h.max(); lv['ONL']=ovn.l.min()
    for k,v in lv.items():
        st={'PDH':'--','PDL':'--','ONH':':','ONL':':'}[k]
        ax.axhline(v,color='#555',lw=0.7,ls=st,zorder=1); ax.text(len(b)-0.5,v,k,fontsize=6,color='#555',va='bottom',ha='right')
    if len(rth):
        ro=rth.o.iloc[0]; ax.axhline(ro,color='#1f4e79',lw=0.7,zorder=1); ax.text(0,ro,'RTH open',fontsize=6,color='#1f4e79',va='bottom')
        vw=rth.vrw.resample(tf,label='right',closed='right').last().reindex(b.index)
        ax.plot(range(len(b)),vw.values,color='#e08a00',lw=0.9,zorder=4)
    # x ticks hourly
    ticks=[i for i,t in enumerate(b.index) if t.minute==0]; ax.set_xticks(ticks); ax.set_xticklabels([b.index[i].strftime('%H:%M') for i in ticks],fontsize=6)
    ax.tick_params(axis='y',labelsize=6)
    A=g.atrD.iloc[-1]; ax.set_title(f"{pd.Timestamp(sd).date()} ({pd.Timestamp(sd).day_name()[:3]})  ATR {A:.0f}  RTH range {rth.h.max()-rth.l.min():.0f}",fontsize=8)
def sheet(days,fname,**kw):
    fig,axs=plt.subplots(2,2,figsize=(14,8.5))
    for ax,sd in zip(axs.flat,days): day_chart(ax,sd,**kw)
    fig.tight_layout(); fig.savefig(fname,dpi=110); plt.close(fig)
if __name__=='__main__':
    mode=sys.argv[1]; seed=int(sys.argv[2]); n=int(sys.argv[3])
    days=df[(df.sd>='2023-01-03')&(df.sd<'2024-01-01')&df.rth].groupby('sd').size()
    days=days[days>=380].index
    rng=np.random.default_rng(seed); pick=sorted(rng.choice(days,4*n,replace=False))
    for j in range(n):
        if mode=='day': sheet(pick[4*j:4*j+4],f'charts/day_{seed}_{j}.png')
        else: sheet(pick[4*j:4*j+4],f'charts/open1m_{seed}_{j}.png',tf='1min',start='09:15',end='11:30')
    print(pick)
