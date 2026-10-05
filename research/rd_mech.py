"""Compare entry mechanisms A/C/D/E on the pooled 5 deviation cells, same risk definition (0.1 ATR) and targets."""
from rangelib import *
build_all()
CELLS=[('OVERNIGHT 18-09:30',0.5),('LONDON 02-08:30',1.0),('OR15',1.5),('PRIOR DAY RTH',0.25),('BOX 30 bars <0.10 ATR',1.5)]
def pool(fn):
    out=[]
    for nm,k in CELLS:
        out+=fn(RANGES[nm].astype(np.float64),k)
    E=np.array(out); o_=np.argsort(E[:,0],kind='stable'); E=E[o_]
    _,u=np.unique(E[:,0],return_index=True); E=E[u]
    return E
def yearly(name,T):
    rr=[]
    for y in (2023,2024,2025):
        x=T[T.ts.dt.year==y]; s=stats(x); ss=streak_stats(x)
        rr.append(f"{y}: N{s['N']} WR {s['WR']:.0f} PF {s['PF']:.2f} Exp {s['ExpR']:+.3f} LS {ss['maxLS']}")
    print(f"{name:55s} | "+" | ".join(rr))
for tgt in (2.0,1e6):
    print(f"\n===== target {'2R' if tgt<1e5 else 'EOD'}, risk = 0.1 ATR =====")
    # A: stop entry at the deviation level (first touch)
    E=pool(lambda R,k: [ (e[0],e[1],e[2]) for e in first_touches(h,l,R,k,0,A)])
    t=E[:,0].astype(np.int64); lv=E[:,1]; d=E[:,2]; ok=~np.isnan(A[t]); t,lv,d=t[ok],lv[ok],d[ok]
    pxL=np.where(d>0,lv,np.nan); pxS=np.where(d<0,lv,np.nan); sL=np.where(d>0,lv-0.1*A[t],np.nan); sS=np.where(d<0,lv+0.1*A[t],np.nan)
    yearly('A stop-entry at deviation (touch)',run_oco(df,t-1,pxL,sL,pxS,sS,expiry=t,rr=tgt))
    # C: close beyond -> market next open
    E=pool(lambda R,k: close_events(h,l,c,R,k,0,10)); t=E[:,0].astype(np.int64); d=E[:,1]; lv=E[:,3]; ok=~np.isnan(A[t]); t,d,lv=t[ok],d[ok],lv[ok]
    yearly('C close beyond deviation -> market',run2(df,t,d,c[t]-d*0.1*A[t],rr=tgt))
    # D: close beyond, then LIMIT back at the deviation level (retest) valid 15 bars
    yearly('D break(close)+retest LIMIT at deviation, 15 bars',run2(df,t,d,lv-d*0.1*A[t],rr=tgt,etype=np.ones(len(t),np.int64),epx=lv,expiry=np.minimum(t+15,df.flat_rth.values[t])))
    # E/F: sweep beyond deviation, close back inside within 10 bars -> reversal
    E=pool(lambda R,k: close_events(h,l,c,R,k,1,10)); t=E[:,0].astype(np.int64); d=E[:,1]; ok=~np.isnan(A[t]); t,d=t[ok],d[ok]
    yearly('E/F sweep & reclaim -> reversal (market)',run2(df,t,d,c[t]-d*0.1*A[t],rr=tgt))
