"""Concept test without cell selection: pool ALL range types at a given deviation k (decided from 2023 observation)."""
from rangelib import *
build_all()
for k in (0.5,1.0,1.5):
    out=[]
    for nm,R in RANGES.items():
        out+=list(close_events(h,l,c,R.astype(np.float64),float(k),0,10))
    E=np.array(out); o_=np.argsort(E[:,0],kind='stable'); E=E[o_]; _,u=np.unique(E[:,0],return_index=True); E=E[u]
    t=E[:,0].astype(np.int64); d=E[:,1]; lv=E[:,3]; ok=~np.isnan(A[t]); t,d,lv=t[ok],d[ok],lv[ok]
    for lab,T in (('C 0.1ATR stop, 2R',run2(df,t,d,c[t]-d*0.1*A[t],rr=2.0)),('C 0.1ATR stop, 1.5R',run2(df,t,d,c[t]-d*0.1*A[t],rr=1.5)),
                  ('C 0.1ATR stop, EOD',run2(df,t,d,c[t]-d*0.1*A[t],rr=1e6)),
                  ('D retest-limit, 0.1ATR, EOD',run2(df,t,d,lv-d*0.1*A[t],rr=1e6,etype=np.ones(len(t),np.int64),epx=lv,expiry=np.minimum(t+15,df.flat_rth.values[t])))):
        rr=[]
        for y in (2023,2024,2025):
            x=T[T.ts.dt.year==y]; s=stats(x); ss=streak_stats(x); rr.append(f"{y}: N{s['N']} WR {s['WR']:.0f} PF {s['PF']:.2f} Exp {s['ExpR']:+.3f} LS {ss['maxLS']}")
        print(f"ALL ranges k={k} {lab:28s} | "+" | ".join(rr))
