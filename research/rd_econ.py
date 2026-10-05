"""Economics of the concept 'close beyond k*W deviation (all ranges) -> continuation'. Stops from MAE, targets from MFE."""
from rangelib import *
build_all()
def concept(k):
    out=[]
    for nm,R in RANGES.items():
        R=R.astype(np.float64)
        for e in close_events(h,l,c,R,float(k),0,10): out.append((e[0],e[1],e[2],e[3],nm))
    E=pd.DataFrame(out,columns=['t','d','W','lv','rng']).sort_values('t',kind='stable').drop_duplicates('t')
    E=E[~np.isnan(A[E.t.values.astype(int)])]
    return E
for k in (1.0,1.5):
    E=concept(k); t=E.t.values.astype(np.int64); d=E.d.values; W=E.W.values; lv=E.lv.values
    # MAE/MFE map (unconstrained to EOD, from next open) in ATR units
    ent=o[t+1]; fl=df.flat_rth.values
    mfe=np.array([((h[tt+1:fl[tt]+1].max()-ent[i]) if d[i]>0 else (ent[i]-l[tt+1:fl[tt]+1].min()))/A[tt] for i,tt in enumerate(t)])
    mae=np.array([((ent[i]-l[tt+1:fl[tt]+1].min()) if d[i]>0 else (h[tt+1:fl[tt]+1].max()-ent[i]))/A[tt] for i,tt in enumerate(t)])
    print(f"\n########## k={k}: events {len(t)} | unconstrained to EOD: MFE median {np.median(mfe):.2f} ATR (P75 {np.quantile(mfe,.75):.2f}), MAE median {np.median(mae):.2f} ATR (P25 {np.quantile(mae,.25):.2f})")
    print(" share of events whose MAE stays below x ATR:",{x:round(float((mae<x).mean()),2) for x in (0.05,0.1,0.15,0.2,0.3)})
    rows=[]
    STOP={'0.05ATR':c[t]-d*0.05*A[t],'0.10ATR':c[t]-d*0.10*A[t],'0.15ATR':c[t]-d*0.15*A[t],'dev level -0.25W':lv-d*0.25*W}
    for sn,st in STOP.items():
        Rr=(c[t]-st)*d; g=(Rr>=0.02*A[t])&(Rr<=0.8*A[t])
        EX={'1R':(None,dict(t1=0)),'2R':('R2',dict()),'3R':('R3',dict()),'next dev (+0.5W)':('ND',dict()),'EOD':(None,dict()),
            'partial 50% @1R +BE, runner EOD':(None,dict(t1=1.0,frac1=0.5,be=True)),'partial 50% @1R, runner EOD (no BE)':(None,dict(t1=1.0,frac1=0.5,be=False))}
        for en,(tp_mode,kw) in EX.items():
            Rabs=np.abs(c[t]-st)
            if en=='1R': tp=c[t]+d*1.0*Rabs
            elif tp_mode=='R2': tp=c[t]+d*2*Rabs
            elif tp_mode=='R3': tp=c[t]+d*3*Rabs
            elif tp_mode=='ND': tp=lv+d*0.5*W
            else: tp=None
            T=run_mp(df,t[g],d[g],st[g],tp_abs=None if tp is None else tp[g],**kw)
            for y in (2023,2024,2025):
                x=T[T.ts.dt.year==y]; s=stats(x); ss=streak_stats(x)
                rows.append(dict(stop=sn,exit=en,yr=y,N=s['N'],WR=s['WR'],avgW=s['AvgWinR'],avgL=s['AvgLossR'],PF=s['PF'],Exp=s['ExpR'],maxLS=ss['maxLS'],avgLS=ss['avgLS'],maxDD=ss['maxDD'],medSL=s['medR'],
                                 MFE=round(x.mfeR.mean(),2),MAE=round(x.maeR.mean(),2),hold=round(x.bars.mean(),0),TPD=s['TPD']))
    R=pd.DataFrame(rows); R.to_csv(f'rd_econ_k{k}.csv',index=False)
    P=R.pivot_table(index=['stop','exit'],columns='yr',values=['Exp','PF','WR','maxLS']); P.columns=[f'{a}{str(b)[2:]}' for a,b in P.columns]
    P['minExp']=P[['Exp23','Exp24','Exp25']].min(axis=1)
    pd.set_option('display.width',260); print(P.round(3).sort_values('minExp',ascending=False).to_string())
