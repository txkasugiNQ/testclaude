"""Market Profile '80% rule' test. Prior RTH value area (70% volume) from 1m bars (volume spread uniformly over bar range)."""
from families3 import *
R_=df[rth]
VA={}
for sd,g in R_.groupby('sd'):
    lo_=g.l.min(); n=int(round((g.h.max()-lo_)*4))+1; vv=np.zeros(n)
    li=np.round((g.l.values-lo_)*4).astype(int); hi=np.round((g.h.values-lo_)*4).astype(int)
    for a_,b_,v_ in zip(li,hi,g.v.values): vv[a_:b_+1]+=v_/(b_-a_+1)
    p=vv.argmax(); tot=vv.sum(); s=vv[p]; i_=j_=p
    while s<0.7*tot:
        up=vv[j_+1] if j_+1<n else -1; dn=vv[i_-1] if i_>0 else -1
        if up>=dn: j_+=1; s+=up
        else: i_-=1; s+=dn
    VA[sd]=(lo_+i_/4,lo_+j_/4,lo_+p/4)
VAs=pd.DataFrame(VA,index=['val','vah','poc']).T.shift(1)   # prior day's VA, known before today
val=df.sd.map(VAs.val).values; vah=df.sd.map(VAs.vah).values
ropen=np.where(rth,pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values,np.nan)
# 30-min period closes at 10:00,10:30,...,15:30 (close-time mod multiples of 30 after 570)
per_end=rth&(m%30==0)&(m>=600)&(m<=930)
rows=[]
for y_ in (2023,2024,2025):
  res=[]
  for sd,g in df[per_end&(df.ts.dt.year==y_)].groupby('sd'):
    idx=g.index.values; ro=ropen[idx[0]]; L_=val[idx[0]]; H_=vah[idx[0]]
    if np.isnan(L_) or np.isnan(ro) or np.isnan(A[idx[0]]): continue
    if L_<=ro<=H_: continue
    side=1 if ro<L_ else -1     # open below VA -> long toward VAH when accepted inside
    inside=(c[idx]>=L_)&(c[idx]<=H_)
    for k in range(1,len(idx)):
        if inside[k] and inside[k-1]:
            t=idx[k]; tgt=H_ if side>0 else L_
            for stop_mode in ('edge','half'):
                st=(L_-0.05*A[t]) if (side>0 and stop_mode=='edge') else (H_+0.05*A[t]) if stop_mode=='edge' else None
                if stop_mode=='half': st=c[t]-side*0.5*abs(tgt-c[t])
                Rr=(c[t]-st)*side; Tt=abs(tgt-c[t])
                if Rr<=0.02*A[t] or Tt<=0: continue
                T=run2(df,np.array([t]),np.array([float(side)]),np.array([st]),rr=Tt/Rr)
                if len(T): res.append((stop_mode,T.pnlR.iloc[0],T.win.iloc[0],Tt/Rr,T.code.iloc[0]))
            break
  X=pd.DataFrame(res,columns=['stop','pnlR','win','rr','code'])
  for sm,gx in X.groupby('stop'):
      gw=gx.pnlR[gx.pnlR>0].sum(); gl=-gx.pnlR[gx.pnlR<0].sum()
      rows.append(dict(year=y_,stop=sm,N=len(gx),WR=round(gx.win.mean()*100,1),medRR=round(gx.rr.median(),2),PF=round(gw/gl,2) if gl>0 else np.inf,ExpR=round(gx.pnlR.mean(),3),target_hit=round((gx.code==1).mean()*100,1)))
print(pd.DataFrame(rows).to_string(index=False))
