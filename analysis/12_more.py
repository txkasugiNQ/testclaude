import pandas as pd, numpy as np
df=pd.read_pickle('nq2.pkl'); D=pd.read_pickle('daily.pkl')
fullsd=D.index[(D.rn==390)&D.atr14.notna()]
G={sd:g for sd,g in df[df.sd.isin(fullsd)&(df.ss=='RTH')].groupby('sd')}
# VWAP band by year
for band in [2.0,2.5,3.0]:
    out={}
    for sd,r in G.items():
        tp=((r.h+r.l+r.c)/3).values; v=r.v.values; cv=np.cumsum(v); vw=np.cumsum(tp*v)/cv
        sdv=np.sqrt(np.maximum(np.cumsum(v*tp*tp)/cv-vw**2,0)); h=r.h.values;l=r.l.values;mm=r['mod'].values
        for sgn in (1,-1):
            lvl=vw+sgn*band*sdv; hit=((h>=lvl) if sgn>0 else (l<=lvl))&(mm>600)
            if not hit.any(): continue
            t=np.argmax(hit); ext=lvl[t]+sgn*sdv[t]; tgt=vw[t]
            for j in range(t+1,len(h)):
                if (sgn>0 and h[j]>=ext) or (sgn<0 and l[j]<=ext): out.setdefault(sd.year,[]).append(0);break
                if (sgn>0 and l[j]<=tgt) or (sgn<0 and h[j]>=tgt): out.setdefault(sd.year,[]).append(1);break
    print(f"VWAP {band}σ  RW-baseline {1/(1+band):.3f}:", {y:(len(x),round(np.mean(x),3)) for y,x in sorted(out.items())})
# Volume climax at new RTH extremes (after 10:00): does extreme hold rest of day?
df['tod']=(df['mod'])
avgv=df[df.sd.isin(fullsd)].groupby(['sd','mod']).v.sum().unstack()
# rolling 20-day time-of-day volume average, shifted (no lookahead)
tv=avgv.rolling(20,min_periods=10).mean().shift(1)
rows=[]
for sd,r in G.items():
    if sd not in tv.index: continue
    h=r.h.values;l=r.l.values;v=r.v.values;mm=r['mod'].values;A=D.at[sd,'atr14']
    base=tv.loc[sd].reindex(mm).values
    rv=v/base
    ch=np.maximum.accumulate(h); cl=np.minimum.accumulate(l)
    for i in range(31,len(h)-30):           # new extreme after 10:00, before 15:30
        if h[i]==ch[i] and h[i]>ch[i-1]:
            rows.append(('H',rv[i],h[i+1:].max()<=h[i], (h[i+1:].max()-h[i])/A, mm[i]))
        if l[i]==cl[i] and l[i]<cl[i-1]:
            rows.append(('L',rv[i],l[i+1:].min()>=l[i], (l[i]-l[i+1:].min())/A, mm[i]))
X=pd.DataFrame(rows,columns=['side','rv','held','furtherA','mod']).dropna()
X['rvb']=pd.cut(X.rv,[0,1,2,3,5,100])
print("\nNew RTH extreme (10:00-15:30): P(extreme holds for rest of RTH) by relative volume of the bar")
print(X.groupby('rvb',observed=True).agg(N=('held','size'),P_hold=('held','mean'),med_further_ATR=('furtherA','median')).round(3))
X['hr']=(X['mod']-1)//60
print(X.groupby('hr').held.agg(['size','mean']).round(3))
# short horizon autocorrelation (RTH 1m,5m,15m returns)
r1=np.log(df.c).diff()
rth=df.ss=='RTH'
for k in [1,5,15,30]:
    x=df[rth].set_index('ts').c.resample(f'{k}min').last().dropna(); rr=np.log(x).diff().dropna()
    print(f"{k}m return lag1 autocorr: {rr.autocorr(1):+.3f}")
