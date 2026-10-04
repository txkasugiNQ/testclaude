"""2023-only: compression box OCO breakout. Box = range of last N bars (incl. t) < q*ATR."""
from families2 import *
P=('2022-12-01','2024-01-01')
def box_signals(N,q,W,stopmode='opp',minw=0.02):
    H=hhv(h,N); L=llv(l,N); wd=H-L
    arm=W&(wd<q*A)&(wd>=minw*A)
    i=np.where(arm)[0]
    pxL=H[i]+TICK; pxS=L[i]-TICK
    if stopmode=='opp': slL=L[i]-TICK; slS=H[i]+TICK
    else: mid=(H[i]+L[i])/2; slL=mid; slS=mid
    return i,pxL,slL,pxS,slS
rows=[]
for N in (15,30,60):
  for q in (0.05,0.08,0.1,0.15):
    for sm in ('opp','mid'):
      i,pL,sL,pS,sS=box_signals(N,q,win(575,930),sm)
      for rr in (1,2,3,1e6):
        T=run_oco(df,i,pL,sL,pS,sS,rr=rr); T=T[(T.sd>=P[0])&(T.sd<P[1])]
        if len(T)<30: continue
        s=stats2(T)
        rows.append(dict(N=N,q=q,stop=sm,rr='EOD' if rr>1e5 else rr,trades=s['N'],TPD=s['TPD'],WR=s['WR'],PF=s['PF'],Exp=s['ExpR'],DD=s['MaxDD_R'],Sh=s['SharpeD'],medR=s['medR']))
R=pd.DataFrame(rows); pd.set_option('display.width',250)
print(R.sort_values('Sh',ascending=False).head(30).to_string(index=False))
print("\nmean Sharpe by param:"); 
for p in ['N','q','stop','rr']: print(p,R.groupby(p).Sh.mean().round(2).to_dict())
