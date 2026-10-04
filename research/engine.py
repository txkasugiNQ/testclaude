"""Core: data arrays, causal features, trade simulator, walk-forward helpers.
Conventions
- CSV timestamp = bar CLOSE time (ET). Signal is evaluated on the CLOSE of bar t (all info <= t).
- Market entry fills at OPEN of bar t+1 (+1 tick slippage). Limit entry fills only if price trades THROUGH
  the limit by 1 tick (conservative); fill price = limit.
- SL = stop order, exit at stop -1 tick slippage (or at bar open if gapped through).
- TP = limit at entry +/- 0.6R, requires trade-through by 1 tick.
- SL and TP touched in the same bar => counted as SL (conservative). On a limit-fill bar only SL is checked.
- Forced flat at session end (RTH strategies: close of the 15:59 ET bar) at close -1 tick.
- Commission+fees 0.25 pt round trip (~$5 NQ). Win = net PnL > 0.
"""
import numpy as np, pandas as pd, numba as nb, os
TICK=0.25; COMM=0.25; RR=0.6
HERE=os.path.dirname(os.path.abspath(__file__))

def load():
    p=os.path.join(HERE,'bars.pkl')
    if os.path.exists(p): return pd.read_pickle(p)
    df=pd.read_csv(os.path.join(HERE,'..','Dataset_NQ_1min_2022_2025 (1).csv'))
    df.columns=['ts','o','h','l','c','v','vr','ve']
    df['ts']=pd.to_datetime(df['ts'],format='%m/%d/%Y %H:%M')
    m=(df.ts.dt.hour*60+df.ts.dt.minute).values; df['mod']=m
    d=df.ts.dt.normalize(); df['sd']=pd.to_datetime(np.where(m>17*60,d+pd.Timedelta(days=1),d))
    df['rth']=(m>570)&(m<=960)
    df.to_pickle(p); return df

@nb.njit(cache=True)
def simulate(o,h,l,c,sig,dirn,etype,epx,stop,expiry,flat,rr,tick,comm):
    """sig: bar index of signal close (sorted). etype 0=market next open, 1=limit at epx.
    stop: absolute stop price (R = |fill-stop|). expiry: last bar index a limit may fill.
    flat[i]: index of forced-exit bar for a trade alive at bar i. One position at a time."""
    n=len(sig); out=np.full((n,7),np.nan)   # entry_i, exit_i, fill, R, pnl, code, sig_i
    busy=-1; k=0
    for s in range(n):
        t=sig[s]
        if t<=busy: continue
        d=dirn[s]; st=stop[s]
        # ---- entry
        if etype[s]==0:
            j=t+1
            if j>=len(o) or j>flat[t]: continue
            fill=o[j]+d*tick
            first=j; chk_tp_first=True
        else:
            px=epx[s]; j=t+1; fill=np.nan
            while j<=expiry[s] and j<=flat[t]:
                if (d>0 and l[j]<=px-tick) or (d<0 and h[j]>=px+tick):
                    fill=px; break
                j+=1
            if np.isnan(fill):
                busy=min(expiry[s],flat[t])   # order was pending until expiry: block signals meanwhile (causal)
                continue
            first=j; chk_tp_first=False
        R=(fill-st)*d
        if R<=tick: continue
        tp=fill+d*rr*R
        fe=flat[first]; code=-1; ex=np.nan; e=first
        while e<=fe:
            if d>0:
                slh = l[e]<=st; tph = h[e]>=tp+tick
            else:
                slh = h[e]>=st; tph = l[e]<=tp-tick
            if e==first and not chk_tp_first: tph=False
            if slh:
                gap = (o[e]<st) if d>0 else (o[e]>st)
                ex=(o[e] if (gap and e!=first) else st)-d*tick; code=0; break
            if tph:
                ex=tp; code=1; break
            e+=1
        if code==-1:
            e=fe; ex=c[e]-d*tick; code=2
        pnl=(ex-fill)*d-comm
        out[k,0]=first; out[k,1]=e; out[k,2]=fill; out[k,3]=R; out[k,4]=pnl; out[k,5]=code; out[k,6]=t
        k+=1; busy=e
    return out[:k]

def run(df,sig,dirn,stop,etype=None,epx=None,expiry=None,flat=None,rr=RR):
    n=len(sig)
    if etype is None: etype=np.zeros(n,np.int64)
    if epx is None: epx=np.full(n,np.nan)
    if expiry is None: expiry=np.asarray(sig,np.int64)
    if flat is None: flat=df['flat_rth'].values
    order=np.argsort(sig,kind='stable')
    r=simulate(df.o.values,df.h.values,df.l.values,df.c.values,np.asarray(sig,np.int64)[order],
               np.asarray(dirn,np.float64)[order],np.asarray(etype,np.int64)[order],np.asarray(epx,np.float64)[order],
               np.asarray(stop,np.float64)[order],np.asarray(expiry,np.int64)[order],np.asarray(flat,np.int64),rr,TICK,COMM)
    T=pd.DataFrame(r,columns=['ei','xi','fill','R','pnl','code','si'])
    for k in ['ei','xi','code','si']: T[k]=T[k].astype(int)
    T['dir']=np.asarray(dirn)[order][np.searchsorted(np.asarray(sig)[order],T.si.values)] if len(T) else []
    T['ts']=df.ts.values[T.ei.values]; T['sd']=df.sd.values[T.ei.values]
    T['win']=T.pnl>0; T['pnlR']=T.pnl/T.R
    return T

def stats(T,days=None):
    if len(T)==0: return dict(N=0,WR=np.nan)
    w=T.win.values; pr=T.pnlR.values
    gw=pr[pr>0].sum(); gl=-pr[pr<0].sum()
    eq=np.cumsum(pr); dd=(np.maximum.accumulate(eq)-eq).max()
    # streaks
    def streak(x):
        best=cur=0
        for v in x:
            cur=cur+1 if v else 0; best=max(best,cur)
        return best
    nd=days if days else T.sd.nunique()
    return dict(N=len(T),WR=round(w.mean()*100,2),PF=round(gw/gl,2) if gl>0 else np.inf,
                ExpR=round(pr.mean(),3),AvgWinR=round(pr[pr>0].mean(),3) if (pr>0).any() else np.nan,
                AvgLossR=round(pr[pr<=0].mean(),3) if (pr<=0).any() else np.nan,
                MaxDD_R=round(dd,1),MaxLS=streak(~w),MaxWS=streak(w),
                TPD=round(len(T)/nd,2),timeexit=round((T.code==2).mean()*100,1),medR=round(T.R.median(),1))

# walk-forward: train 12 months rolling, test next quarter
def wf_windows():
    q=pd.date_range('2024-01-01','2026-01-01',freq='QS')
    return [(a-pd.DateOffset(months=12),a,b) for a,b in zip(q[:-1],q[1:])]
