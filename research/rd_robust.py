from rangelib import *
trades=pd.read_pickle('tr5_concept.pkl')
Rr=df[rth].groupby('sd').agg(rh=('h','max'),rl=('l','min'),ro=('o','first'),rc=('c','last')); daytype=((Rr.rc-Rr.ro).abs()/(Rr.rh-Rr.rl))
for key in ('{"k": 1.5, "stop": 0.1, "exit": "EOD"}','{"k": 1.0, "stop": 0.15, "exit": "P+BE"}'):
    T=trades[key].copy(); si=T.si.values
    print(f"\n######## {key}")
    s=stats(T); ss=streak_stats(T); print(f"ALL: N={s['N']} WR={s['WR']} avgW={s['AvgWinR']} avgL={s['AvgLossR']} PF={s['PF']} Exp={s['ExpR']:+.3f} maxDD={ss['maxDD']} avgDD={ss['avgDD']} maxLS={ss['maxLS']} avgLS={ss['avgLS']} TPD={s['TPD']} medSL={s['medR']}pts meanSL={T.R.mean():.1f}pts MFE={T.mfeR.mean():.2f}R MAE={T.maeR.mean():.2f}R hold={T.bars.mean():.0f}min")
    T['vol']=pd.qcut(pd.Series(A[si]).rank(pct=True),3,labels=['lowATR','midATR','highATR']).values
    print("by ATR tercile:",T.groupby('vol',observed=True).pnlR.agg(['size','mean']).round(3).to_dict('index'))
    mo=T.groupby(T.ts.dt.to_period('M')).pnlR.sum(); print(f"months positive: {(mo>0).mean()*100:.0f}% of {len(mo)} | worst month {mo.min():.1f}R best {mo.max():.1f}R")
    dt=pd.cut(T.sd.map(daytype).values,[0,0.3,0.6,1.0],labels=['range day','normal','trend day'])
    print("day type (ex-post, report only):",T.groupby(dt,observed=True).pnlR.agg(['size','mean']).round(3).to_dict('index'))
    T['dow']=T.ts.dt.day_name().str[:3]; print("weekday:",T.groupby('dow').pnlR.mean().round(3).to_dict())
