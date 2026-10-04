"""Bar-by-bar replica of the 'NQ Momentum Levels' Pine indicator (MBL + OBR modules).
Evaluated strictly on bar close, state machine identical to the Pine code."""
from mbl import *
from families3 import _pack_rr
flat=df.flat_rth.values
def replica_mbl(TH=0.12,N=5,VALID=5,tick=0.25,slip=0.25,comm=0.25,w=(575,930)):
    pend=0; px=sl=np.nan; expb=-1; pos=0; entry=stop=R=np.nan; eb=-1; busy=-1; trades=[]
    for t in range(N+1,len(c)):
        # 1) pending stop order
        if pend!=0:
            if (pend>0 and l[t]<=sl) or (pend<0 and h[t]>=sl):          # invalidation before entry (same bar = cancel)
                pend=0; busy=t
            elif (pend>0 and h[t]>=px) or (pend<0 and l[t]<=px):
                entry=(max(px,o[t]) if pend>0 else min(px,o[t]))+pend*slip; pos=pend; stop=sl; R=(entry-stop)*pos; eb=t; pend=0
                if R<=tick: pos=0; busy=t
            elif t>=expb:
                pend=0; busy=t
        # 2) position management
        if pos!=0:
            hit=(l[t]<=stop) if pos>0 else (h[t]>=stop)
            ex=None
            if hit:
                gap=(o[t]<stop) if pos>0 else (o[t]>stop)
                ex=(o[t] if (gap and t!=eb) else stop)-pos*slip
            elif t>=flat[eb]: ex=c[t]-pos*slip
            if ex is not None:
                trades.append((eb,t,entry,R,(ex-entry)*pos-comm,pos)); pos=0; busy=t
        # 3) new burst signal
        if pend==0 and pos==0 and t>busy and rth[t] and w[0]<m[t]<=w[1] and not np.isnan(A[t]):
            thr=TH*A[t]; r0=c[t]-c[t-N]; r1=c[t-1]-c[t-1-N]
            d=1 if (r0>thr and r1<=thr) else (-1 if (r0<-thr and r1>=-thr) else 0)
            if d!=0:
                hi=h[t-4:t+1].max(); lo=l[t-4:t+1].min()
                if 0.02*A[t]<=hi-lo<=0.6*A[t] and t+1<=flat[t]:
                    pend=d; px=hi+tick if d>0 else lo-tick; sl=lo-tick if d>0 else hi+tick; expb=min(t+VALID,flat[t])
    return pd.DataFrame(trades,columns=['ei','xi','fill','R','pnl','dir'])
def replica_obr(K=0.03,tick=0.25,slip=0.25,comm=0.25):
    pend=0; pos=0; trades=[]; st=np.nan
    for t in range(1,len(c)):
        if pend!=0:
            entry=o[t]+pend*slip; pos=pend; stop=st; R=(entry-stop)*pos; eb=t; pend=0
            if R<=tick: pos=0
        if pos!=0:
            ex=None
            if (l[t]<=stop) if pos>0 else (h[t]>=stop):
                gap=(o[t]<stop) if pos>0 else (o[t]>stop)
                ex=(o[t] if (gap and t!=eb) else stop)-pos*slip
            elif t>=flat[eb]: ex=c[t]-pos*slip
            if ex is not None: trades.append((eb,t,entry,R,(ex-entry)*pos-comm,pos)); pos=0
        if m[t]==571 and not np.isnan(A[t]) and pos==0:
            body=c[t]-o[t]
            if abs(body)>K*A[t]:
                d=1 if body>0 else -1; s_=l[t]-tick if d>0 else h[t]+tick; Re=(c[t]-s_)*d
                if 0.02*A[t]<=Re<=0.6*A[t] and t+1<=flat[t]: pend=d; st=s_
    return pd.DataFrame(trades,columns=['ei','xi','fill','R','pnl','dir'])
if __name__=='__main__':
    E=mbl(0.12,EOD,cancel=True); P=replica_mbl()
    ok=len(E)==len(P) and (E.ei.values==P.ei.values).all() and (E.xi.values==P.xi.values).all() and np.allclose(E.pnl.values,P.pnl.values)
    print(f"MBL: engine {len(E)} / replica {len(P)} identical={ok}")
    if not ok:
        mm=min(len(E),len(P)); k=np.argmax((E.ei.values[:mm]!=P.ei.values[:mm])|(E.xi.values[:mm]!=P.xi.values[:mm])|~np.isclose(E.pnl.values[:mm],P.pnl.values[:mm])); print(E.iloc[k-1:k+2][['ei','xi','fill','R','pnl','si']]); print(P.iloc[k-1:k+2])
    i=np.where((m==571)&~np.isnan(A))[0]; i=i[np.abs(c[i]-o[i])>0.03*A[i]]; d=np.sign(c[i]-o[i])
    E2=_pack_rr(i,d,np.where(d>0,l[i]-TICK,h[i]+TICK),EOD,0); P2=replica_obr()
    ok2=len(E2)==len(P2) and (E2.ei.values==P2.ei.values).all() and (E2.xi.values==P2.xi.values).all() and np.allclose(E2.pnl.values,P2.pnl.values)
    print(f"OBR: engine {len(E2)} / replica {len(P2)} identical={ok2}")
    if not ok2:
        mm=min(len(E2),len(P2)); k=np.argmax((E2.ei.values[:mm]!=P2.ei.values[:mm])|(E2.xi.values[:mm]!=P2.xi.values[:mm])); print(E2.iloc[k-1:k+2]); print(P2.iloc[k-1:k+2])
