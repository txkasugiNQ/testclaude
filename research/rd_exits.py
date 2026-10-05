"""Exit/stop economics for pooled 'close beyond extended deviation -> continuation' (5 cells), realistic fills (run2: market next open +1 tick)."""
from rangelib import *
build_all()
CELLS=[('OVERNIGHT 18-09:30',0.5),('LONDON 02-08:30',1.0),('OR15',1.5),('PRIOR DAY RTH',0.25),('BOX 30 bars <0.10 ATR',1.5)]
T_=[];D_=[];LV=[];ED=[];W_=[]
for nm,k in CELLS:
    R=RANGES[nm].astype(np.float64)
    ev=np.array(close_events(h,l,c,R,k,0,10)); t=ev[:,0].astype(np.int64)
    for j,tt in enumerate(t):
        r=[rr for rr in R if rr[3]<=tt<=rr[4]][-1]
        T_.append(tt); D_.append(ev[j,1]); LV.append(ev[j,3]); ED.append(r[0] if ev[j,1]>0 else r[1]); W_.append(ev[j,2])
T_=np.array(T_,np.int64); D_=np.array(D_); LV=np.array(LV); ED=np.array(ED); W_=np.array(W_)
o_=np.argsort(T_,kind='stable'); T_,D_,LV,ED,W_=T_[o_],D_[o_],LV[o_],ED[o_],W_[o_]
ok=~np.isnan(A[T_]); T_,D_,LV,ED,W_=T_[ok],D_[ok],LV[ok],ED[ok],W_[ok]
# de-duplicate events on the same bar
_,u=np.unique(T_,return_index=True); T_,D_,LV,ED,W_=T_[u],D_[u],LV[u],ED[u],W_[u]
STOPS={'deviation level -0.05ATR (back inside dev)':LV-D_*0.05*A[T_],
       'midway dev/edge':(LV+ED)/2,
       'range edge (back into range)':ED,
       '0.1 ATR from close':c[T_]-D_*0.1*A[T_],
       'swing 10 bars':np.where(D_>0,LLV[10][T_]-TICK,HHV[10][T_]+TICK)}
rows=[]
for sn,st in STOPS.items():
    Rr=(c[T_]-st)*D_; good=(Rr>=0.02*A[T_])&(Rr<=0.8*A[T_])
    for tgt in (1.0,1.5,2.0,3.0,1e6):
        T=run2(df,T_[good],D_[good],st[good],rr=tgt)
        for y in (2023,2024,2025):
            x=T[T.ts.dt.year==y]; s=stats(x); ss=streak_stats(x)
            rows.append(dict(stop=sn,tgt='EOD' if tgt>1e5 else tgt,yr=y,N=s['N'],WR=s['WR'],avgW=s['AvgWinR'],avgL=s['AvgLossR'],PF=s['PF'],Exp=s['ExpR'],maxLS=ss['maxLS'],medSL=s['medR']))
R=pd.DataFrame(rows)
P=R.pivot_table(index=['stop','tgt'],columns='yr',values=['Exp','PF','WR','maxLS','medSL']); P.columns=[f'{a}{str(b)[2:]}' for a,b in P.columns]
P['minExp']=P[['Exp23','Exp24','Exp25']].min(axis=1)
pd.set_option('display.width',260); print(P.round(3).sort_values('minExp',ascending=False).to_string())
print("\nevents total:",len(T_),"per active day ~",round(len(T_)/len(np.unique(df.sd.values[T_])),2))
