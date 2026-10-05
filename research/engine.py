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

@nb.njit(cache=True)
def simulate2(o,h,l,c,sig,dirn,etype,epx,stop,expiry,flat,rr,be_at,trail_k,max_bars,tick,comm):
    """Like simulate() plus management (all decided with info up to the PREVIOUS bar's close):
    rr: target in R (>=1e5 = no target); be_at: move stop to entry+1tick once MFE >= be_at R (0=off);
    trail_k: stop trails at best extreme since entry -/+ trail_k R (0=off); max_bars: time stop (0=off).
    Stop updates take effect from the NEXT bar (conservative). Same-bar SL+TP => SL."""
    n=len(sig); out=np.full((n,8),np.nan); busy=-1; k=0
    for s in range(n):
        t=sig[s]
        if t<=busy: continue
        d=dirn[s]; st=stop[s]
        if etype[s]==0:
            j=t+1
            if j>=len(o) or j>flat[t]: continue
            fill=o[j]+d*tick; chk=True
        else:
            px=epx[s]; j=t+1; fill=np.nan
            while j<=expiry[s] and j<=flat[t]:
                if (d>0 and l[j]<=px-tick) or (d<0 and h[j]>=px+tick):
                    fill=px; break
                j+=1
            if np.isnan(fill):
                busy=min(expiry[s],flat[t]); continue
            chk=False
        R=(fill-st)*d
        if R<=tick: continue
        tp=fill+d*rr*R; first=j; fe=flat[first]; e=first; code=-1; ex=np.nan
        cur=st; best=fill
        while e<=fe:
            if d>0: slh=l[e]<=cur; tph=h[e]>=tp+tick
            else:   slh=h[e]>=cur; tph=l[e]<=tp-tick
            if e==first and not chk: tph=False
            if slh:
                gap=(o[e]<cur) if d>0 else (o[e]>cur)
                ex=(o[e] if (gap and e!=first) else cur)-d*tick; code=0; break
            if tph:
                ex=tp; code=1; break
            if max_bars>0 and e-first+1>=max_bars:
                ex=c[e]-d*tick; code=3; break
            # update management state with this (completed) bar -> effective next bar
            best=max(best,h[e]) if d>0 else min(best,l[e])
            mfe=(best-fill)*d/R
            if be_at>0 and mfe>=be_at:
                nb_=fill+d*tick
                cur=max(cur,nb_) if d>0 else min(cur,nb_)
            if trail_k>0:
                ts=best-d*trail_k*R
                cur=max(cur,ts) if d>0 else min(cur,ts)
            e+=1
        if code==-1:
            e=fe; ex=c[e]-d*tick; code=2
        out[k,0]=first; out[k,1]=e; out[k,2]=fill; out[k,3]=R; out[k,4]=(ex-fill)*d-comm; out[k,5]=code; out[k,6]=t; out[k,7]=d
        k+=1; busy=e
    return out[:k]

def run2(df,sig,dirn,stop,rr=1e6,be_at=0.0,trail_k=0.0,max_bars=0,etype=None,epx=None,expiry=None,flat=None):
    n=len(sig)
    if n==0: return pd.DataFrame(columns=['ei','xi','fill','R','pnl','code','si','dir','ts','sd','win','pnlR'])
    if etype is None: etype=np.zeros(n,np.int64)
    if epx is None: epx=np.full(n,np.nan)
    if expiry is None: expiry=np.asarray(sig,np.int64)
    if flat is None: flat=df['flat_rth'].values
    order=np.argsort(sig,kind='stable')
    r=simulate2(df.o.values,df.h.values,df.l.values,df.c.values,np.asarray(sig,np.int64)[order],
               np.asarray(dirn,np.float64)[order],np.asarray(etype,np.int64)[order],np.asarray(epx,np.float64)[order],
               np.asarray(stop,np.float64)[order],np.asarray(expiry,np.int64)[order],np.asarray(flat,np.int64),
               float(rr),float(be_at),float(trail_k),int(max_bars),TICK,COMM)
    T=pd.DataFrame(r,columns=['ei','xi','fill','R','pnl','code','si','dir'])
    for kk in ['ei','xi','code','si']: T[kk]=T[kk].astype(int)
    T['ts']=df.ts.values[T.ei.values]; T['sd']=df.sd.values[T.ei.values]
    T['win']=T.pnl>0; T['pnlR']=T.pnl/T.R
    return T

def stats2(T,days=None):
    """stats + PF in points (equal 1 contract) and daily-R Sharpe"""
    s=stats(T,days)
    if len(T)==0: return s
    gp=T.pnl[T.pnl>0].sum(); gl=-T.pnl[T.pnl<0].sum()
    s['PF_pts']=round(gp/gl,2) if gl>0 else np.inf
    dr=T.groupby('sd').pnlR.sum()
    s['SharpeD']=round(dr.mean()/dr.std()*np.sqrt(252),2) if dr.std()>0 else np.nan
    return s

@nb.njit(cache=True)
def simulate_oco(o,h,l,c,sig,pxL,slL,pxS,slS,expiry,flat,rr,max_bars,tick,comm,slip_ticks,cancel_inv=False):
    """OCO bracket of STOP-entry orders placed at close of bar sig[s], valid bars sig+1..expiry[s].
    Long fills if high >= pxL at max(pxL, open) + slippage; short symmetric. If both trigger in the same
    bar, the side whose trigger is nearer the bar open is assumed first (the other side is cancelled),
    and on the fill bar only the stop is checked (conservative). rr>=1e5 -> no target (hold to flat/time stop)."""
    n=len(sig); out=np.full((n,8),np.nan); busy=-1; k=0; sl=slip_ticks*tick
    for s in range(n):
        t=sig[s]
        if t<=busy: continue
        j=t+1; d=0.0; fill=np.nan; st=np.nan
        cancelled=False
        while j<=expiry[s] and j<=flat[t]:
            lt=(not np.isnan(pxL[s])) and h[j]>=pxL[s]
            stt=(not np.isnan(pxS[s])) and l[j]<=pxS[s]
            if cancel_inv:
                # invalidation: protective-stop level traded before the entry level -> cancel (conservative: same bar = cancel)
                invL=(not np.isnan(pxL[s])) and l[j]<=slL[s]
                invS=(not np.isnan(pxS[s])) and h[j]>=slS[s]
                if (invL and np.isnan(pxS[s])) or (invS and np.isnan(pxL[s])):
                    cancelled=True; break
            if lt and stt:
                if abs(o[j]-pxL[s])<=abs(o[j]-pxS[s]): stt=False
                else: lt=False
            if lt:
                d=1.0; fill=max(pxL[s],o[j])+sl; st=slL[s]; break
            if stt:
                d=-1.0; fill=min(pxS[s],o[j])-sl; st=slS[s]; break
            j+=1
        if cancelled:
            busy=j; continue
        if d==0.0:
            busy=min(expiry[s],flat[t]); continue
        R=(fill-st)*d
        if R<=tick:
            busy=j; continue
        tp=fill+d*rr*R; first=j; fe=flat[first]; e=first; code=-1; ex=np.nan
        while e<=fe:
            if d>0: slh=l[e]<=st; tph=h[e]>=tp+tick
            else:   slh=h[e]>=st; tph=l[e]<=tp-tick
            if e==first: tph=False
            if slh:
                gap=(o[e]<st) if d>0 else (o[e]>st)
                ex=(o[e] if (gap and e!=first) else st)-d*sl; code=0; break
            if tph:
                ex=tp; code=1; break
            if max_bars>0 and e-first+1>=max_bars:
                ex=c[e]-d*sl; code=3; break
            e+=1
        if code==-1:
            e=fe; ex=c[e]-d*sl; code=2
        out[k,0]=first; out[k,1]=e; out[k,2]=fill; out[k,3]=R; out[k,4]=(ex-fill)*d-comm; out[k,5]=code; out[k,6]=t; out[k,7]=d
        k+=1; busy=e
    return out[:k]

def run_oco(df,sig,pxL,slL,pxS,slS,expiry=None,rr=1e6,max_bars=0,flat=None,slip_ticks=1,cancel_inv=False):
    sig=np.asarray(sig,np.int64); n=len(sig)
    cols=['ei','xi','fill','R','pnl','code','si','dir']
    if n==0: return pd.DataFrame(columns=cols+['ts','sd','win','pnlR'])
    if expiry is None: expiry=sig+1
    if flat is None: flat=df['flat_rth'].values
    order=np.argsort(sig,kind='stable')
    f=lambda x: np.asarray(x,np.float64)[order]
    r=simulate_oco(df.o.values,df.h.values,df.l.values,df.c.values,sig[order],f(pxL),f(slL),f(pxS),f(slS),
                   np.asarray(expiry,np.int64)[order],np.asarray(flat,np.int64),float(rr),int(max_bars),TICK,COMM,int(slip_ticks),bool(cancel_inv))
    T=pd.DataFrame(r,columns=cols)
    for kk in ['ei','xi','code','si']: T[kk]=T[kk].astype(int)
    T['ts']=df.ts.values[T.ei.values]; T['sd']=df.sd.values[T.ei.values]
    T['win']=T.pnl>0; T['pnlR']=T.pnl/T.R
    return T

@nb.njit(cache=True)
def simulate_oco2(o,h,l,c,sig,pxL,slL,pxS,slS,expiry,flat,stop_frac,t1,frac1,be,t2,tick,comm,slip_ticks):
    """OCO stop-entry (same fill/cancel rules as simulate_oco with invalidation) + management:
    stop placed at fill - d*stop_frac*R0 (R0 = distance fill->structural stop); partial exit of frac1 at t1*R (limit,
    trade-through 1 tick); after t1 is hit the remaining stop moves to entry+1tick (if be) from the NEXT bar;
    remainder exits at t2*R (>=1e5: none) or stop or session flat. pnl reported per 1 unit (weighted), R = actual risk."""
    n=len(sig); out=np.full((n,9),np.nan); busy=-1; k=0; sl=slip_ticks*tick
    for s in range(n):
        t=sig[s]
        if t<=busy: continue
        j=t+1; d=0.0; fill=np.nan; st0=np.nan; cancelled=False
        while j<=expiry[s] and j<=flat[t]:
            lt=(not np.isnan(pxL[s])) and h[j]>=pxL[s]
            stt=(not np.isnan(pxS[s])) and l[j]<=pxS[s]
            invL=(not np.isnan(pxL[s])) and l[j]<=slL[s]
            invS=(not np.isnan(pxS[s])) and h[j]>=slS[s]
            if (invL and np.isnan(pxS[s])) or (invS and np.isnan(pxL[s])):
                cancelled=True; break
            if lt and stt:
                if abs(o[j]-pxL[s])<=abs(o[j]-pxS[s]): stt=False
                else: lt=False
            if lt:
                d=1.0; fill=max(pxL[s],o[j])+sl; st0=slL[s]; break
            if stt:
                d=-1.0; fill=min(pxS[s],o[j])-sl; st0=slS[s]; break
            j+=1
        if cancelled:
            busy=j; continue
        if d==0.0:
            busy=min(expiry[s],flat[t]); continue
        R0=(fill-st0)*d
        if R0<=tick:
            busy=j; continue
        R=stop_frac*R0
        if R<=2*tick:
            busy=j; continue
        cur=fill-d*R; tp1=fill+d*t1*R; tp2=fill+d*t2*R
        first=j; fe=flat[first]; e=first; part=False; pnl=0.0; rem=1.0; code=-1; mae=0.0; mfe=0.0; pend_be=False
        while e<=fe:
            if pend_be:
                cur=max(cur,fill+tick) if d>0 else min(cur,fill-tick); pend_be=False
            adv=(fill-l[e]) if d>0 else (h[e]-fill); fav=(h[e]-fill) if d>0 else (fill-l[e])
            slh=(l[e]<=cur) if d>0 else (h[e]>=cur)
            h1=(not part) and t1>0 and (((h[e]>=tp1+tick) if d>0 else (l[e]<=tp1-tick)))
            h2=t2<1e5 and (((h[e]>=tp2+tick) if d>0 else (l[e]<=tp2-tick)))
            if e==first: h1=False; h2=False
            if slh:
                gap=(o[e]<cur) if d>0 else (o[e]>cur)
                ex=(o[e] if (gap and e!=first) else cur)-d*sl
                pnl+=rem*(ex-fill)*d; rem=0.0; code=0
                mae=max(mae,min(adv,R)); break
            mae=max(mae,adv); mfe=max(mfe,fav)
            if h1:
                pnl+=frac1*(tp1-fill)*d; rem-=frac1; part=True
                if be: pend_be=True
                if rem<=1e-9: code=1; break
            if h2:
                pnl+=rem*(tp2-fill)*d; rem=0.0; code=1; break
            e+=1
        if rem>1e-9:
            if e>fe: e=fe
            pnl+=rem*(c[e]-d*sl-fill)*d; code=2 if code==-1 else code
        out[k,0]=first; out[k,1]=e; out[k,2]=fill; out[k,3]=R; out[k,4]=pnl-comm; out[k,5]=code; out[k,6]=t; out[k,7]=d; out[k,8]=mae/R
        k+=1; busy=e
    return out[:k]

def run_oco2(df,sig,pxL,slL,pxS,slS,expiry,stop_frac=1.0,t1=0.0,frac1=0.5,be=False,t2=1e6,flat=None,slip_ticks=1):
    sig=np.asarray(sig,np.int64)
    if flat is None: flat=df['flat_rth'].values
    order=np.argsort(sig,kind='stable'); f=lambda x: np.asarray(x,np.float64)[order]
    r=simulate_oco2(df.o.values,df.h.values,df.l.values,df.c.values,sig[order],f(pxL),f(slL),f(pxS),f(slS),
                    np.asarray(expiry,np.int64)[order],np.asarray(flat,np.int64),float(stop_frac),float(t1),float(frac1),bool(be),float(t2),TICK,COMM,int(slip_ticks))
    T=pd.DataFrame(r,columns=['ei','xi','fill','R','pnl','code','si','dir','maeR'])
    for kk in ['ei','xi','code','si']: T[kk]=T[kk].astype(int)
    T['ts']=df.ts.values[T.ei.values]; T['sd']=df.sd.values[T.ei.values]
    T['win']=T.pnl>0; T['pnlR']=T.pnl/T.R
    return T

def streak_stats(T):
    w=T.win.values; s=0; st=[]
    for v in w:
        if not v: s+=1
        else:
            if s: st.append(s)
            s=0
    if s: st.append(s)
    st=np.array(st) if st else np.array([0])
    eq=np.cumsum(T.pnlR.values); dd=np.maximum.accumulate(eq)-eq
    # average drawdown depth over drawdown episodes
    ep=[]; cur=0
    for x in dd:
        if x>0: cur=max(cur,x)
        elif cur>0: ep.append(cur); cur=0
    if cur>0: ep.append(cur)
    return dict(avgLS=round(st.mean(),2),maxLS=int(st.max()),p90LS=int(np.quantile(st,0.9)),avgDD=round(np.mean(ep) if ep else 0,2),maxDD=round(dd.max(),1))
