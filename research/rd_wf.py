"""Portfolio walk-forward of Range->Deviation->Close continuation family. Selection per quarter from the prior 12 months only."""
from rangelib import *
from wf2 import score, DAYS
import json
build_all()
VARIANTS={'C_0.1A_2R':('C',2.0),'C_0.1A_1.5R':('C',1.5),'C_mid_EOD':('Cmid',1e6),'D_0.1A_EOD':('D',1e6)}
combos={}
for nm,R in RANGES.items():
    R=R.astype(np.float64)
    for k in (0.25,0.5,1.0,1.5):
        ev=close_events(h,l,c,R,float(k),0,10)
        if len(ev)<60: continue
        E=np.array(ev); t=E[:,0].astype(np.int64); d=E[:,1]; lv=E[:,3]; W=E[:,2]
        ok=~np.isnan(A[t]); t,d,lv,W=t[ok],d[ok],lv[ok],W[ok]
        o_=np.argsort(t,kind='stable'); t,d,lv,W=t[o_],d[o_],lv[o_],W[o_]
        edge=lv-d*k*W
        for vn,(mech,tgt) in VARIANTS.items():
            if mech=='C': T=run2(df,t,d,c[t]-d*0.1*A[t],rr=tgt)
            elif mech=='Cmid':
                st=(lv+edge)/2; Rr=(c[t]-st)*d; g=(Rr>=0.02*A[t])&(Rr<=0.8*A[t]); T=run2(df,t[g],d[g],st[g],rr=tgt)
            else: T=run2(df,t,d,lv-d*0.1*A[t],rr=tgt,etype=np.ones(len(t),np.int64),epx=lv,expiry=np.minimum(t+15,df.flat_rth.values[t]))
            if len(T)>30: combos[(nm,k,vn)]=T
print("combos:",len(combos))
nd=df[df.sd>='2024-01-01'].sd.nunique()
for tmin,M in ((1.0,6),(1.5,6),(2.0,6),(1.5,3)):
    oos=[];picks=[]
    for tr0,te0,te1 in wf_windows():
        best={}
        for (nm,k,vn),T in combos.items():
            a=T[(T.sd>=tr0)&(T.sd<te0)]
            if len(a)<40: continue
            s=score(a)
            if s>=tmin and (nm not in best or s>best[nm][0]): best[nm]=(s,k,vn)
        top=sorted(best.items(),key=lambda x:-x[1][0])[:M]
        picks.append((str(te0.date()),[(nm[:10],kk,vn) for nm,(s,kk,vn) in top]))
        for nm,(s,kk,vn) in top:
            b=combos[(nm,kk,vn)]; oos.append(b[(b.sd>=te0)&(b.sd<te1)].assign(cell=f"{nm}|{kk}|{vn}"))
    O=pd.concat(oos).sort_values('ts') if oos else pd.DataFrame()
    s=stats(O,nd); a=stats(O); ss=streak_stats(O)
    py={y:round((lambda x: x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum())(O[O.ts.dt.year==y]),2) for y in (2024,2025)}
    q=O.groupby(O.ts.dt.to_period('Q')).pnlR.sum().round(1).tolist()
    print(f"\nWF portfolio tmin={tmin} M={M}: N={s['N']} WR={s['WR']} avgW={s['AvgWinR']} avgL={s['AvgLossR']} PF={s['PF']} Exp={s['ExpR']:+.3f} maxDD={ss['maxDD']}R avgDD={ss['avgDD']} maxLS={ss['maxLS']} avgLS={ss['avgLS']} TPD(active)={a['TPD']} medSL={s['medR']}pts | PF by year {py}")
    print("   quarterly sumR:",q)
    for p in picks: print("   ",p[0],p[1])
pd.to_pickle(combos,'tr5_rd_combos.pkl')
