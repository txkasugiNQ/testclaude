import pandas as pd, numpy as np
df=pd.read_pickle('nq.pkl'); df['t']=df.ts.dt.strftime('%H:%M')
nz=df[df.vr!=0]
print("vr nonzero time range:", nz.t.min(), nz.t.max()); print(nz.groupby(nz.ts.dt.hour).size())
print(df[(df.ts.dt.date==pd.Timestamp('2024-03-05').date())&(df.t.isin(['09:30','09:31','09:32','15:59','16:00','16:01']))])
# check RTH vwap calc: recompute from 09:31
day=df[(df.ts.dt.date==pd.Timestamp('2024-03-05').date())&(df.t>='09:31')&(df.t<='16:00')].copy()
tp=(day.h+day.l+day.c)/3; day['myv']=(tp*day.v).cumsum()/day.v.cumsum()
print(day[['ts','vr','myv']].iloc[[0,1,10,200,-1]])
# ETH vwap reset time
e=df[(df.ts>='2024-03-05 17:55')&(df.ts<='2024-03-05 18:05')]; print(e)
for d in ['2022-12-30 16:00','2023-06-30 16:00','2023-12-29 16:00','2024-06-28 16:00','2024-12-31 16:00','2025-06-30 16:00','2025-09-30 16:00','2025-12-10 16:00']:
    print(d, df[df.ts==d].c.values)
# roll detection: biggest overnight session gaps near roll weeks
