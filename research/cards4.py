"""Trade-level backtests (realistic fills via engine.run2: market entry next bar open + 1 tick, stop/target conservative) for round-4 chart structures."""
from structlib import *
from openrev import orv
def cardrow(name,T):
    out=[]
    for y in (2023,2024,2025):
        x=T[T.ts.dt.year==y]
        if len(x)==0: continue
        s=stats(x); ss=streak_stats(x)
        out.append(dict(structure=name,year=y,N=s['N'],TPD_active=s['TPD'],WR=s['WR'],avgW=s['AvgWinR'],avgL=s['AvgLossR'],PF=s['PF'],ExpR=s['ExpR'],maxLS=ss['maxLS'],avgLS=ss['avgLS'],maxDD=ss['maxDD'],medSL_pts=s['medR'],medSL_ATR=round(np.median(x.R/A[x.si.values]),3)))
    return out
rows=[]
W=win(575,930)
# S1 FLAG (B2): pole 20 bars >=0.2 ATR, flag 15 bars <=40% of pole, retrace <=50%; trigger close beyond flag; stop beyond flag
P,F,X,q=20,15,0.2,0.4
fh=hhv(h,F); fl=llv(l,F); ph_=prev(hhv(h,P),F); pl_=prev(llv(l,P),F); pc=prev(c,F); pole=ph_-pl_
up=(pole>=X*A)&(pc>=pl_+0.7*pole)&((fh-fl)<=q*pole)&(fl>=ph_-0.5*pole)
dn=(pole>=X*A)&(pc<=ph_-0.7*pole)&((fh-fl)<=q*pole)&(fh<=pl_+0.5*pole)
trL=W&(prev(up.astype(float))==1)&(c>prev(fh)); trS=W&(prev(dn.astype(float))==1)&(c<prev(fl))
i=np.r_[np.where(trL)[0],np.where(trS)[0]]; d=np.r_[np.ones(trL.sum()),-np.ones(trS.sum())]
st=np.where(d>0,prev(fl)[i]-TICK,prev(fh)[i]+TICK)
for rr in (1.0,2.0):
    rows+=cardrow(f'FLAG breakout, stop beyond flag, target {rr}R',run2(df,i,d,st,rr=rr))
calm=(df.atr60.values[i]/df.atr390.values[i])<1
rows+=cardrow('FLAG (calm vol only, post-hoc lead), 1R',run2(df,i[calm],d[calm],st[calm],rr=1.0))
# S2 OPENING REVERSAL (B1): best 2023 config of the level simulator
rows+=cardrow('OPEN REVERSAL, stop-entry at open, stop early extreme, tgt 0.5x',orv(0.15,660,660,'stop',1.0,0.5))
rows+=cardrow('OPEN REVERSAL, close-confirm, stop 0.5x, tgt 0.75x',orv(0.15,660,660,'close',0.5,0.75))
# S3 CLEAN TREND CONTINUATION (motif clusters): first event/day/side, stop beyond 30-min swing, target 1R
dec=rth&(m%5==0)&(m>=690)&(m<=900)&~np.isnan(A)
N=120; H2=hhv(h,N); L2=llv(l,N); net=c-prev(c,N-1); rng=H2-L2; eff=np.abs(net)/rng; pos=(c-L2)/rng
upm=once_per_day(dec&(net>0)&(eff>=0.7)&(rng>=0.25*A)&(pos>=0.85)); dnm=once_per_day(dec&(net<0)&(eff>=0.7)&(rng>=0.25*A)&(pos<=0.15))
i=np.r_[np.where(upm)[0],np.where(dnm)[0]]; d=np.r_[np.ones(upm.sum()),-np.ones(dnm.sum())]
st=np.where(d>0,LLV[30][i]-TICK,HHV[30][i]+TICK)
rows+=cardrow('CLEAN 2h TREND continuation, stop 30m swing, 1R',run2(df,i,d,st,rr=1.0))
R=pd.DataFrame(rows); pd.set_option('display.width',260); print(R.to_string(index=False)); R.to_csv('cards4.csv',index=False)
