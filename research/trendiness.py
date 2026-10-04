from families2 import *
R=df[rth].copy(); R['r1']=np.log(R.c).diff(); R.loc[R['mod']==571,'r1']=np.nan
R['b30']=(R['mod']-571)//30
r30=R.groupby(['sd','b30']).r1.sum()
day=pd.DataFrame({'v1':R.groupby('sd').r1.var(),'v30':r30.groupby(level=0).var(),'n1':R.groupby('sd').r1.count()})
day['VR']=day.v30/(30*day.v1)
day['A']=df.groupby('sd').atrD.first(); day['month']=day.index.to_period('M')
mo=day.groupby('month').agg(VR=('VR','mean'),A=('A','mean'))
mo['VR_next']=mo.VR.shift(-1)
print(mo.round(3).to_string())
print("\ncorr VR vs ATR level:",round(mo[['VR','A']].corr().iloc[0,1],2),"| autocorr VR month->next:",round(mo.VR.autocorr(1),2))
day['VRprev20']=day.VR.rolling(20).mean().shift(1)
print("daily: corr(VR, mean VR of prior 20 days) =",round(day[['VR','VRprev20']].corr().iloc[0,1],3))
print("mean VR by year:",day.groupby(day.index.year).VR.mean().round(3).to_dict())
