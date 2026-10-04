"""2023-only exploration of management styles on momentum bursts and PDH/PDL breakouts"""
from families2 import *
P=('2022-12-01','2024-01-01')
def show(name,sig,d,st):
    rows=[]
    for rr,be,tr,mb in [(1e6,0,0,0),(2,0,0,0),(3,0,0,0),(1e6,1,0,0),(1e6,0,1,0),(1e6,0,1.5,0),(1e6,0,2,0),(1e6,1,2,0),(3,1,0,0),(1e6,0,0,60),(1e6,0,0,120)]:
        T=run2(df,sig,d,st,rr=rr,be_at=be,trail_k=tr,max_bars=mb); T=T[(T.sd>=P[0])&(T.sd<P[1])]
        s=stats2(T); rows.append(dict(rr='∞' if rr>1e5 else rr,be=be,trail=tr,tstop=mb,N=s['N'],WR=s['WR'],PF=s['PF'],Exp=s['ExpR'],DD=s['MaxDD_R'],Sh=s['SharpeD']))
    print("\n##",name); print(pd.DataFrame(rows).to_string(index=False))
for th in (0.16,0.25):
    s=f6(th=th,stp='sw5',w='all'); show(f"burst th{th} sw5 all-day",s['sig'],s['dir'],s['stop'])
W=win(575,930)
iL=np.where(first_cross(LEV['PDH'],1,W))[0]; iS=np.where(first_cross(LEV['PDL'],-1,W))[0]
sig=np.r_[iL,iS]; d=np.r_[np.ones(len(iL)),-np.ones(len(iS))]; st=np.r_[LLV[5][iL]-TICK,HHV[5][iS]+TICK]
R=(c[sig]-st)*d; k=(R>=0.02*A[sig])&(R<=0.5*A[sig]); show("PDH/PDL breakout sw5",sig[k],d[k],st[k])
