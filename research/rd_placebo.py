from rangelib import *
rng=np.random.default_rng(0)
for y in (2023,2024,2025):
    cand=np.where(rth&(m>590)&(m<=900)&(YR==y)&~np.isnan(A))[0]; t0=rng.choice(cand,6000,replace=False)
    ts=[];lv=[];dd=[]
    for t in t0:
        d=rng.choice([-1.0,1.0]); L_=c[t]+d*rng.uniform(0.02,0.15)*A[t]
        w=np.arange(t+1,min(t+90,flat[t]-29))
        hit=(h[w]>=L_) if d>0 else (l[w]<=L_)
        if hit.any(): ts.append(w[np.argmax(hit)]); lv.append(L_); dd.append(d)
    ts=np.array(ts,np.int64); lv=np.array(lv); dd=np.array(dd)
    for lab,s in (('0.1ATR',0.1*A[ts]),('0.05ATR',0.05*A[ts])):
        cr,rr,_,_=touch_outcomes(o,h,l,c,ts,lv,dd,s,s,flat,TICK)
        print(f"{y} PLACEBO random levels s={lab}: CONT {np.mean(cr[cr!=0]>0):.3f}  REV {np.nanmean(rr[(rr!=0)&~np.isnan(rr)]>0):.3f}  N={len(ts)}")
