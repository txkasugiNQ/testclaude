"""B4 'Afternoon return to VWAP after a strong morning trend'. Decision at fixed times; target = VWAP (natural), stop = beyond day extreme (+k ATR)."""
from structlib import *
ropen=np.where(rth,pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values,np.nan)
rh_,rl_=df.rh.values,df.rl.values
rows=[]
for T0 in (720,780,840):
  for x in (0.3,0.5):
    for buf in (0.0,0.05):
      i=np.where(rth&(m==T0)&~np.isnan(A))[0]
      mv=(c[i]-ropen[i])/A[i]; pos=(c[i]-rl_[i])/(rh_[i]-rl_[i])
      sel=((mv>x)&(pos>0.75))|((mv<-x)&(pos<0.25)); i=i[sel]; d=-np.sign(mv[sel])        # fade
      ent=c[i]; tgt=vrw[i]; a=np.abs(ent-tgt)
      st=np.where(d<0,rh_[i]+buf*A[i]+TICK,rl_[i]-buf*A[i]-TICK); b=np.abs(st-ent)
      ok=(a>0.02*A[i])&(b>0.02*A[i]); i,d,ent,a,b=i[ok],d[ok],ent[ok],a[ok],b[ok]
      r,mae,mfe=first_hit(h,l,i.astype(np.int64),d,ent,a,b,flat)
      for y in (2023,2024,2025):
        k=(YR[i]==y)&(r!=0)
        if k.sum()<10: continue
        p=(r[k]>0).mean(); rw=(b/(a+b))[k].mean()
        rows.append(dict(time=f"{T0//60}:{T0%60:02d}",move=x,buf=buf,yr=y,N=int(k.sum()),P=round(p,3),RW=round(rw,3),edge_pp=round(100*(p-rw),1),RR=round(np.median(a[k]/b[k]),2),timeouts=round((r[YR[i]==y]==0).mean(),2)))
R=pd.DataFrame(rows); print(R.pivot_table(index=['time','move','buf'],columns='yr',values=['edge_pp','N','P','RR']).round(2).to_string())
