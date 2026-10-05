"""Walk-forward over the fixed CONCEPT (all ranges pooled, close beyond k*W -> continuation); only k/stop/exit selected per quarter."""
from rangelib import *
from wf2 import wf, stats2
import json
build_all()
def concept_events(k):
    out=[]
    for nm,R in RANGES.items():
        for e in close_events(h,l,c,R.astype(np.float64),float(k),0,10): out.append((e[0],e[1],e[2],e[3]))
    E=np.array(out); E=E[np.argsort(E[:,0],kind='stable')]; _,u=np.unique(E[:,0],return_index=True); E=E[u]
    t=E[:,0].astype(np.int64); ok=~np.isnan(A[t])&(t+1<=df.flat_rth.values[t]); return t[ok],E[ok,1]
EXITS={'2R':dict(tp=2.0),'3R':dict(tp=3.0),'EOD':dict(),'P+BE':dict(t1=1.0,frac1=0.5,be=True),'P':dict(t1=1.0,frac1=0.5,be=False)}
trades={}
for k in (1.0,1.5):
    t,d=concept_events(k)
    for sk in (0.10,0.15):
        st=c[t]-d*sk*A[t]
        for en,kw in EXITS.items():
            kw=dict(kw); tp=kw.pop('tp',None)
            T=run_mp(df,t,d,st,tp_abs=None if tp is None else c[t]+d*tp*np.abs(c[t]-st),**kw)
            trades[json.dumps({'k':k,'stop':sk,'exit':en})]=T
pd.to_pickle(trades,'tr5_concept.pkl')
nd=df[df.sd>='2024-01-01'].sd.nunique()
for fmin in (0.5,1.0,1.5):
    O,sel=wf(trades,fmin); s=stats2(O,nd); a=stats2(O); ss=streak_stats(O)
    py={y:round((lambda x: x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum())(O[O.ts.dt.year==y]),2) for y in (2024,2025)}
    print(f"\nWF concept fmin={fmin}: N={s['N']} WR={s['WR']} avgW={s['AvgWinR']} avgL={s['AvgLossR']} PF={s['PF']} Exp={s['ExpR']:+.3f} maxDD={ss['maxDD']}R avgDD={ss['avgDD']} maxLS={ss['maxLS']} avgLS={ss['avgLS']} TPD(active)={a['TPD']} medSL={s['medR']}pts SharpeD={s['SharpeD']} | PF/yr {py}")
    print("   quarterly sumR:",O.groupby(O.ts.dt.to_period('Q')).pnlR.sum().round(1).tolist())
    for x in sel: print("    ",x[0],x[1],x[4],x[5])
# session / hour breakdown for two reference variants (fixed)
for key in ('{"k": 1.5, "stop": 0.1, "exit": "EOD"}','{"k": 1.0, "stop": 0.15, "exit": "P+BE"}','{"k": 1.5, "stop": 0.15, "exit": "3R"}'):
    T=trades[key].copy(); mm=m[T.ei.values]
    T['session']=pd.cut(mm,[0,510,570,600,690,840,961],labels=['London 02-08:30','NY pre 08:30-09:30','NY open 09:30-10:00','NY AM 10-11:30','NY mid 11:30-14','NY PM 14-16'])
    print(f"\n{key}: ExpR (N) by session x year")
    print(T.pivot_table(index='session',columns=T.ts.dt.year,values='pnlR',aggfunc=['mean','size'],observed=True).round(3).to_string())
