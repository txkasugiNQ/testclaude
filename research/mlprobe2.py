from families2 import *
import lightgbm as lgb, warnings; warnings.filterwarnings('ignore')
flat=df.flat_rth.values
cand=np.where(rth&(m>=575)&(m<=900)&(m%5==0)&~np.isnan(A))[0]
H=60
ent=o[cand+1]; ex=c[np.minimum(cand+H,flat[cand])]; y=(ex-ent)/A[cand]
ropen=np.where(rth,pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values,np.nan)
first=pd.Series(np.where(m==572,c-o,np.nan)).groupby(df.sd.values).transform('max').values  # 09:31 bar? use 09:30 bar body
ob=pd.Series(np.where(m==571,c-o,np.nan)).groupby(df.sd.values).transform('max').values
F=df.iloc[cand]; Ac=A[cand]; cc=c[cand]
def d(x): return (cc-x[cand])/Ac
X=pd.DataFrame({'mod':m[cand],'dow':F.ts.dt.dayofweek.values,
 'mv_open':d(ropen),'gap':(ropen[cand]-pcl[cand])/Ac,'ob':ob[cand]/Ac,
 'dPDH':d(LEV['PDH']),'dPDL':d(LEV['PDL']),'dONH':d(ONH),'dONL':d(ONL),'dIBH':d(orH[60]),'dIBL':d(orL[60]),'dPWH':d(PWH),'dPWL':d(PWL),
 'vwd':(cc-vrw[cand])/vrs[cand],'vwa':(cc-vrw[cand])/Ac,'ru':(df.rh.values[cand]-df.rl.values[cand])/Ac,'pos':(cc-df.rl.values[cand])/(df.rh.values[cand]-df.rl.values[cand]),
 'r5':df.ret5.values[cand]/Ac,'r15':df.ret15.values[cand]/Ac,'r30':df.ret30.values[cand]/Ac,'r60':df.ret60.values[cand]/Ac,
 'comp30':(hhv(h,30)[cand]-llv(l,30)[cand])/Ac,'comp60':(hhv(h,60)[cand]-llv(l,60)[cand])/Ac,
 'vr':df.atr60.values[cand]/df.atr390.values[cand],'a14':df.atr14.values[cand]/Ac,'A':Ac/cc,
 'e50_200':(df.ema50.values[cand]-df.ema200.values[cand])/Ac,'c500':(cc-df.ema500.values[cand])/Ac,'reg':REG[cand],'z240':df.z240.values[cand]})
ts=F.ts.reset_index(drop=True); cost=0.75/Ac
res=[]
for tr0,te0,te1 in wf_windows():
    tr=((ts>=tr0)&(ts<te0-pd.Timedelta(days=1))).values; te=((ts>=te0)&(ts<te1)).values
    mdl=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.03,num_leaves=15,min_child_samples=300,subsample=0.7,subsample_freq=1,colsample_bytree=0.7,verbose=-1)
    mdl.fit(X[tr],y[tr]); ptr=mdl.predict(X[tr]); pte=mdl.predict(X[te])
    for q in (0.5,0.8,0.9,0.95):
        th=np.quantile(np.abs(ptr),q); sel=np.abs(pte)>=th
        r=np.sign(pte[sel])*y[te][sel]-cost[te][sel]
        res.append((str(te0.date()),q,sel.sum(),r.sum(),(r>0).sum(),r[r>0].sum(),-r[r<0].sum()))
Rr=pd.DataFrame(res,columns=['win','q','n','sum','wins','gp','gl'])
G=Rr.groupby('q').sum(numeric_only=True); G['meanATR%']=(G['sum']/G.n*100).round(2); G['WR']=(G.wins/G.n*100).round(1); G['PF']=(G.gp/G.gl).round(2)
print(G[['n','meanATR%','WR','PF']])
print("\nper-quarter mean (q=0.9):",Rr[Rr.q==0.9].assign(mn=lambda x:(x['sum']/x.n*100).round(2))[['win','n','mn']].to_string(index=False))
# importance on full training through 2024 (no OOS use for decisions beyond inspiration)
tr=(ts<'2025-01-01').values
mdl=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.03,num_leaves=15,min_child_samples=300,subsample=0.7,subsample_freq=1,colsample_bytree=0.7,verbose=-1,importance_type='gain')
mdl.fit(X[tr],y[tr]); imp=pd.Series(mdl.feature_importances_,index=X.columns).sort_values(ascending=False); print((imp/imp.sum()*100).round(1).head(12).to_string())
# univariate: decile of top features vs mean fwd return (2023 vs 2024)
for f in imp.index[:6]:
    b=pd.qcut(X[f],10,labels=False,duplicates='drop'); t=pd.DataFrame({'b':b,'y':y,'yr':ts.dt.year})
    print(f, (t[t.yr==2023].groupby('b').y.mean()*100).round(1).tolist(),'|',(t[t.yr==2024].groupby('b').y.mean()*100).round(1).tolist(),'|',(t[t.yr==2025].groupby('b').y.mean()*100).round(1).tolist())
