from families import *
import lightgbm as lgb, warnings; warnings.filterwarnings('ignore')
# broad F14 signal set, simulated WITHOUT position constraint (each signal its own trade) for labeling
s=f14(n=10,th=0.08,ret=0.5,kst=0.0,tf='none',w='all')
# simulate each signal independently: call run per signal is slow -> run with staggered single-position by splitting into chunks of non-overlap? simpler: loop numba per signal via large flat
import engine
res=[]
for j in range(len(s['sig'])):
    pass
# vectorized approach: simulate each signal separately using simulate on 1-element arrays (numba fast)
o_,h_,l_,c_=o,h,l,c; fl=df.flat_rth.values
out=np.full((len(s['sig']),7),np.nan)
for j in range(len(s['sig'])):
    r=engine.simulate(o_,h_,l_,c_,s['sig'][j:j+1].astype(np.int64),s['dir'][j:j+1].astype(float),np.ones(1,np.int64),s['epx'][j:j+1],s['stop'][j:j+1],s['expiry'][j:j+1].astype(np.int64),fl,0.6,TICK,COMM)
    if len(r): out[j]=r[0]
ok=~np.isnan(out[:,0]); print("signals",len(ok),"filled",ok.sum())
i=s['sig'][ok]; d=s['dir'][ok]; win_=(out[ok,4]>0).astype(int)
F=df.iloc[i].reset_index(drop=True); Aa=F.atrD.values
X=pd.DataFrame({'d':d,'vds':d*(F.c-F.vrw)/F.vrs,'z60':d*F.z60,'z240':d*F.z240,'rsi70':d*(F.rsi70-50),
 'r15':d*F.ret15/Aa,'r60':d*F.ret60/Aa,'e50_200':d*(F.ema50-F.ema200)/Aa,'c500':d*(F.c-F.ema500)/Aa,
 'pos':(F.c-F.sl)/(F.sh-F.sl),'ru':(F.sh-F.sl)/Aa,'vr1':F.atr60/F.atr390,'a14':F.atr14/Aa,'mod':F['mod'],
 'dpc':d*(F.c-F.pcl)/Aa,'reg':REG[i]*d,'R':(np.abs(s['epx'][ok]-s['stop'][ok]))/Aa,'vrel':vrel[i]})
ts=F.ts; rows=[]
for tr0,te0,te1 in wf_windows():
    trm=((ts>=tr0)&(ts<te0-pd.Timedelta(days=1))).values; tem=((ts>=te0)&(ts<te1)).values
    mdl=lgb.LGBMClassifier(n_estimators=200,learning_rate=0.03,num_leaves=15,min_child_samples=100,subsample=0.7,subsample_freq=1,colsample_bytree=0.7,verbose=-1)
    mdl.fit(X[trm],win_[trm]); ptr=mdl.predict_proba(X[trm])[:,1]; pte=mdl.predict_proba(X[tem])[:,1]
    for q in (0,0.5,0.75,0.9,0.95):
        thr=np.quantile(ptr,q) if q>0 else -1; sel=pte>=thr
        rows.append((q,sel.sum(),win_[tem][sel].sum()))
Q=pd.DataFrame(rows,columns=['q','n','w']).groupby('q').sum(); nd=df[df.sd>='2024-01-01'].sd.nunique()
Q['OOS_WR']=(Q.w/Q.n*100).round(1); Q['signals_per_day']=(Q.n/nd).round(2); print(Q)
