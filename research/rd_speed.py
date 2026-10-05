"""Quantify visual observation: slow (accepted) vs fast (spike) arrival at the deviation."""
from rangelib import *
build_all()
CELLS=[('OVERNIGHT 18-09:30',0.5),('LONDON 02-08:30',1.0),('OR15',1.5),('PRIOR DAY RTH',0.25),('BOX 30 bars <0.10 ATR',1.5)]
a14=df.atr14.values
rows=[]
for nm,k in CELLS:
    R=RANGES[nm].astype(np.float64)
    ev=np.array(close_events(h,l,c,R,k,0,10)); t=ev[:,0].astype(np.int64); d=ev[:,1]; W=ev[:,2]
    # bars since price first closed outside the range edge (acceptance time), per event
    acc=np.zeros(len(t))
    for j,(tt,dd) in enumerate(zip(t,d)):
        r=[rr for rr in R if rr[3]<=tt<=rr[4]][-1]; edge=r[0] if dd>0 else r[1]
        seg=c[int(r[3]):tt+1]; out=(seg>edge) if dd>0 else (seg<edge)
        acc[j]=len(seg)-np.argmax(out) if out.any() else 0
    for tt,dd,ww,aa in zip(t,d,W,acc):
        rows.append(dict(cell=f"{nm} k{k}",t=tt,d=dd,yr=YR[tt],bar=abs(c[tt]-o[tt])/a14[tt],vel=dd*(c[tt]-c[tt-15])/A[tt],acc=aa,mod=m[tt]))
E=pd.DataFrame(rows); E=E[~np.isnan(A[E.t.values])]
E['res']=sym_from_close(o,h,l,c,E.t.values.astype(np.int64),E.d.values,0.1*A[E.t.values],flat)
E=E[E.res!=0]; E['win']=E.res>0
E['barQ']=pd.qcut(E.bar,3,labels=['small bar','mid bar','big bar'])
E['velQ']=pd.qcut(E.vel,3,labels=['slow','mid','fast'])
E['accQ']=pd.cut(E.acc,[-1,5,30,10000],labels=['<=5 bars outside','6-30','>30 bars outside'])
E['tod']=pd.cut(E['mod'],[0,600,690,840,960],labels=['<=10:00','10:00-11:30','11:30-14:00','14:00-16:00'])
for col in ('barQ','velQ','accQ','tod'):
    print(f"\n-- pooled 5 cells, win share at +-0.1 ATR from decision close, by {col} (RW 0.50) --")
    print(E.pivot_table(index=col,columns='yr',values='win',aggfunc=['mean','size'],observed=True).round(3).to_string())
E.to_pickle('rd_speed_events.pkl')
