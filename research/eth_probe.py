from labels import *
import lightgbm as lgb, warnings; warnings.filterwarnings('ignore')
df=build(); m=df['mod'].values
# all bars of the ETH session except last 30 min, flat at session end (17:00)
cand=np.where(~np.isnan(df.atrD.values)&~((m>16*60+30)&(m<=17*60)))[0]
cand=cand[::3]   # subsample every 3rd bar for speed
F=df.iloc[cand].reset_index(drop=True); A=F.atrD; c=F.c
res={}
for k in (0.05,0.1):
    out,_=lab(df.o.values,df.h.values,df.l.values,df.c.values,cand,k*df.atrD.values[cand],df.flat_eth.values,RR,TICK,COMM)
    res[k]=out
# WR by hour-of-day (ET, bar start), long/short
hr=((F['mod']-1)%1440)//60
for k,out in res.items():
    t=pd.DataFrame({'hr':hr,'L':out[:,0],'S':out[:,1],'is':F.ts<'2024-01-01'})
    print(f"R={k}A  by hour  (IS 2023 | OOS 2024-25)")
    g=t.groupby(['hr','is'])[['L','S']].mean().unstack().round(3)
    print(g.to_string())
