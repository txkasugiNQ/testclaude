from families import *
s=f14(n=10,th=0.08,ret=0.5,kst=0.0,tf='reg',w='all')
T=run(df,s['sig'],s['dir'],s['stop'],etype=s['etype'],epx=s['epx'],expiry=s['expiry'])
T['per']=np.where(T.sd<'2024-01-01','IS23','OOS2425')
si=T.si.values; Aa=A[si]
T['vol']=pd.qcut(df.sd.map(pd.Series(A,index=df.sd).groupby(level=0).first().rank(pct=True)).values[si],3,labels=['lowvol','midvol','highvol'])
T['hour']=(m[T.ei.values]-1)//60
T['dirn']=np.where(T.dir>0,'long','short')
T['volreg']=pd.cut(df.atr60.values[si]/df.atr390.values[si],[0,0.8,1.2,99],labels=['calm','normal','excited'])
T['ru']=pd.cut((df.sh.values[si]-df.sl.values[si])/Aa,[0,0.5,0.8,1.2,99])
T['dow']=T.ts.dt.dayofweek
T['q']=T.ts.dt.to_period('Q').astype(str)
print("overall",T.groupby('per').win.agg(['size','mean']).round(3).to_string())
for col in ['dirn','vol','volreg','ru','hour','dow']:
    print("\n",col); print(T.groupby([col,'per'],observed=True).win.agg(['size','mean']).unstack().round(3).to_string())
print("\nby quarter:"); print(T.groupby('q').win.agg(['size','mean']).round(3).T.to_string())
