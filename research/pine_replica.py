"""Bar-by-bar replica of the Pine indicator logic (state machine, evaluated on bar close like Pine).
Used to prove the Pine rules == research engine rules."""
from families import *
def replica(window=(575,690),TH=0.16,N=5,SWN=5,rr=0.6,tick=0.25,slip_ticks=1,ttr_ticks=1,comm=0.25,minR=0.03,maxR=0.4):
    sl=slip_ticks*tick; tt=ttr_ticks*tick
    pos=0; entry=stop=tp=R=np.nan; pending=0; trades=[]; ei=-1
    flat=df.flat_rth.values; n=len(c)
    for t in range(n):
        exited=False
        # 1) pending market order fills at this bar's open
        if pending!=0:
            pos=pending; pending=0; entry=o[t]+pos*sl; R=(entry-stop)*pos
            if R<=tick: pos=0
            else: tp=entry+pos*rr*R; ei=t
        # 2) manage open position on this bar
        if pos!=0:
            slh = l[t]<=stop if pos>0 else h[t]>=stop
            tph = h[t]>=tp+tt if pos>0 else l[t]<=tp-tt
            px=None
            if slh:
                gap=(o[t]<stop) if pos>0 else (o[t]>stop)
                px=(o[t] if (gap and t!=ei) else stop)-pos*sl
            elif tph: px=tp
            elif t>=flat[ei]: px=c[t]-pos*sl
            if px is not None:
                trades.append((ei,t,entry,R,(px-entry)*pos-comm,pos)); pos=0; exited=True
        # 3) new signal on bar close (only when flat, not on an exit bar, no pending order)
        if pos==0 and not exited and pending==0 and t>=N+1 and not np.isnan(A[t]) and rth[t] and window[0]<m[t]<=window[1]:
            thr=TH*A[t]; r0=c[t]-c[t-N]; r1=c[t-1]-c[t-1-N]
            d=1 if (r0>thr and r1<=thr) else (-1 if (r0<-thr and r1>=-thr) else 0)
            if d!=0:
                st=(l[t-SWN+1:t+1].min()-tick) if d>0 else (h[t-SWN+1:t+1].max()+tick)
                Re=(c[t]-st)*d
                if minR*A[t]<=Re<=maxR*A[t] and t+1<=flat[t]:
                    pending=d; stop=st
    return pd.DataFrame(trades,columns=['ei','xi','fill','R','pnl','dir'])
if __name__=='__main__':
    import time
    for wname,wv in (('am',(575,690)),('all',(575,930))):
        t0=time.time(); P=replica(window=wv)
        s=f6(th=0.16,stp='sw5',w=wname); E=run(df,s['sig'],s['dir'],s['stop'])
        same=len(P)==len(E) and np.array_equal(P.ei.values,E.ei.values) and np.array_equal(P.xi.values,E.xi.values) and np.allclose(P.pnl.values,E.pnl.values)
        print(f"{wname}: replica {len(P)} trades, engine {len(E)} trades, identical={same}  ({time.time()-t0:.0f}s)")
        if not same:
            mm=min(len(P),len(E)); k=np.argmax((P.ei.values[:mm]!=E.ei.values[:mm])|(P.xi.values[:mm]!=E.xi.values[:mm]))
            print(P.iloc[k-1:k+2]); print(E.iloc[k-1:k+2])
