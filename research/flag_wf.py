from structlib import *
from wf2 import wf, stats2
import json
W_all=win(575,930)
_dc=df[rth].groupby('sd').c.last(); sma20=_dc.rolling(20).mean(); sma50=_dc.rolling(50).mean()
TR20=df.sd.map(np.sign(_dc-sma20).shift(1)).values; TR50=df.sd.map(np.sign(_dc-sma50).shift(1)).values
def flag_trades(P,F,X,q,rr,align,w):
    W=win(*w)
    fh=hhv(h,F); fl=llv(l,F); ph_=prev(hhv(h,P),F); pl_=prev(llv(l,P),F); pc=prev(c,F); pole=ph_-pl_
    up=(pole>=X*A)&(pc>=pl_+0.7*pole)&((fh-fl)<=q*pole)&(fl>=ph_-0.5*pole)
    dn=(pole>=X*A)&(pc<=ph_-0.7*pole)&((fh-fl)<=q*pole)&(fh<=pl_+0.5*pole)
    trL=W&(prev(up.astype(float))==1)&(c>prev(fh)); trS=W&(prev(dn.astype(float))==1)&(c<prev(fl))
    if align=='d20': trL&=TR20==1; trS&=TR20==-1
    if align=='d50': trL&=TR50==1; trS&=TR50==-1
    if align=='vwap': trL&=c>vrw; trS&=c<vrw
    i=np.r_[np.where(trL)[0],np.where(trS)[0]]; d=np.r_[np.ones(trL.sum()),-np.ones(trS.sum())]
    st=np.where(d>0,prev(fl)[i]-TICK,prev(fh)[i]+TICK)
    return run2(df,i,d,st,rr=rr)
# (1) 2023-only: does HTF alignment help?
print("2023 only (discovery) - alignment check, P20 F15 X0.2 q0.4, 1R:")
for al in ('none','d20','d50','vwap'):
    T=flag_trades(20,15,0.2,0.4,1.0,al,(575,930)); x=T[T.ts.dt.year==2023]; s=stats(x)
    print(f"  align={al:5s} N={s['N']} WR={s['WR']} PF={s['PF']} Exp={s['ExpR']:+.3f}")
# (2) walk-forward over a compact flag family
grid=[]
for P,F,X in ((15,10,0.15),(20,15,0.2),(30,20,0.2)):
    for q in (0.4,0.5):
        for rr in (1.0,1.5,2.0):
            for al in ('none','d20','vwap'):
                for w in ((575,930),(575,720),(690,930)):
                    grid.append(dict(P=P,F=F,X=X,q=q,rr=rr,align=al,w=w))
trades={json.dumps({**g,'w':list(g['w'])}):flag_trades(g['P'],g['F'],g['X'],g['q'],g['rr'],g['align'],g['w']) for g in grid}
pd.to_pickle(trades,'tr4_flag.pkl')
nd=df[df.sd>='2024-01-01'].sd.nunique()
for fmin in (0.25,0.5,1.0):
    O,sel=wf(trades,fmin); s=stats2(O,nd); a=stats2(O); ss=streak_stats(O)
    q_=O.groupby(O.ts.dt.to_period('Q')).pnlR.sum().round(1).tolist()
    print(f"\nWF flag family fmin={fmin}: N={s['N']} WR={s['WR']} PF={s['PF']} Exp={s['ExpR']:+.3f} maxLS={ss['maxLS']} avgLS={ss['avgLS']} maxDD={ss['maxDD']} TPD_active={a['TPD']} medSL={s['medR']}pts")
    print("   quarterly sumR:",q_)
    print("   PF 2024 / 2025:",[round(x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum(),2) for x in (O[O.ts.dt.year==2024],O[O.ts.dt.year==2025])])
    for x in sel: print("    ",x[0],x[1],x[4],x[5])
