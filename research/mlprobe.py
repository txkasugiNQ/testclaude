from feats import *
import lightgbm as lgb, warnings; warnings.filterwarnings('ignore')
df=build(); L=pd.read_pickle('labels.pkl')
F=df.iloc[L.i.values].reset_index(drop=True); c=F.c; A=F.atrD
vol=df.v.values; vrel=pd.Series(vol).rolling(30).mean()/pd.Series(vol).rolling(390).mean()
X=pd.DataFrame({
 'vds':(c-F.vrw)/F.vrs,'vda':(c-F.vrw)/A,'eds':(c-F.vew)/F.ves,'eda':(c-F.vew)/A,
 'z20':F.z20,'z60':F.z60,'z240':F.z240,'rsi14':F.rsi14,'rsi70':F.rsi70,
 'r5':F.ret5/A,'r15':F.ret15/A,'r30':F.ret30/A,'r60':F.ret60/A,
 'e9_21':(F.ema9-F.ema21)/A,'e21_50':(F.ema21-F.ema50)/A,'e50_200':(F.ema50-F.ema200)/A,'c200':(c-F.ema200)/A,'c500':(c-F.ema500)/A,
 'pos':(c-F.sl)/(F.sh-F.sl),'posr':(c-F.rl)/(F.rh-F.rl),'ru':(F.sh-F.sl)/A,'rru':(F.rh-F.rl)/A,
 'dsh':(F.sh-c)/A,'dsl':(c-F.sl)/A,'drh':(F.rh-c)/A,'drl':(c-F.rl)/A,
 'vr1':F.atr60/F.atr390,'vr2':F.atr14/F.atr60,'a14':F.atr14/A,'a390':F.atr390/A,'A':A/c,
 'mod':F['mod'],'dow':F.ts.dt.dayofweek,
 'dph':(c-F.ph)/A,'dpl':(c-F.pl)/A,'dpc':(c-F.pcl)/A,
 'dor':np.where(F.or30h.notna(),(c-(F.or30h+F.or30l)/2)/A,np.nan),'orw':(F.or30h-F.or30l)/A,
 'dibh':(c-F.ibh)/A,'dibl':(c-F.ibl)/A,
 'vrel':vrel.values[L.i.values],
 'body':(F.c-F.o)/F.atr14,'uw':(F.h-np.maximum(F.o,F.c))/F.atr14,'lw':(np.minimum(F.o,F.c)-F.l)/F.atr14,
})
ts=F.ts
res=[]
for k in ['0.05','0.1','0.2']:
  for side in ['L','S']:
    y=L[f'{side}{k}'].values
    oos_p=np.full(len(y),np.nan); thr_by_q={}
    allq=[]
    for tr0,te0,te1 in wf_windows():
        tr=((ts>=tr0)&(ts<te0)).values; te=((ts>=te0)&(ts<te1)).values
        # gap of 1 day between train and test to avoid label overlap leakage
        tr=tr&(ts<te0-pd.Timedelta(days=1)).values
        tr=tr&~np.isnan(y); te=te&~np.isnan(y)
        m=lgb.LGBMClassifier(n_estimators=300,learning_rate=0.03,num_leaves=31,min_child_samples=500,subsample=0.7,subsample_freq=1,colsample_bytree=0.7,verbose=-1)
        m.fit(X[tr],y[tr]); ptr=m.predict_proba(X[tr])[:,1]; pte=m.predict_proba(X[te])[:,1]
        oos_p[te]=pte
        for q in (0.5,0.8,0.9,0.95,0.99,0.999):
            thr=np.quantile(ptr,q); sel=pte>=thr
            allq.append((q,sel.sum(),y[te][sel].sum(),te.sum()))
    Q=pd.DataFrame(allq,columns=['q','n','w','tot']).groupby('q').sum()
    for q,r in Q.iterrows():
        res.append((k,side,q,int(r.n),round(r.w/r.n*100,1) if r.n else np.nan))
    print(k,side,"OOS base",round(np.nanmean(y[~np.isnan(oos_p)])*100,1)); 
R=pd.DataFrame(res,columns=['R','side','train_quantile','OOS_n','OOS_WR'])
print(R.to_string())
