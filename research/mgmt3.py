"""Management study on MBL entries: stop fraction x partial/BE x final target. Exploration on 2023, report 2024-25 alongside."""
from mbl import *
i,pL,sL,pS,sS,ex=mbl_orders(0.12)
rows=[]
for sf in (0.5,0.75,1.0):
  for t1,be in ((0,False),(0.5,True),(1.0,True),(1.0,False)):
    for t2 in (1.0,1.5,2.0,3.0,EOD):
      if t1>0 and t2<=t1: continue
      T=run_oco2(df,i,pL,sL,pS,sS,ex,stop_frac=sf,t1=t1,frac1=0.5,be=be,t2=t2)
      for per,(a,b) in (('IS23',('2022-12-01','2024-01-01')),('OOS2425',('2024-01-01','2026-01-01'))):
        x=T[(T.sd>=a)&(T.sd<b)]; s=stats(x); ss=streak_stats(x)
        rows.append(dict(stop=sf,t1=t1,be=be,t2='EOD' if t2>1e5 else t2,per=per,N=s['N'],WR=s['WR'],PF=s['PF'],Exp=s['ExpR'],avgW=s['AvgWinR'],avgL=s['AvgLossR'],**ss,medR=s['medR']))
R=pd.DataFrame(rows); pd.set_option('display.width',260)
P=R.pivot_table(index=['stop','t1','be','t2'],columns='per',values=['WR','PF','Exp','maxLS','avgLS','medR']).round(2)
P.columns=[f'{a}_{b}' for a,b in P.columns]
print(P.sort_values('Exp_IS23',ascending=False).to_string())
R.to_csv('mgmt3.csv',index=False)
