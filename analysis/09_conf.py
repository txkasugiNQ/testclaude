import pandas as pd, numpy as np
exec(open('08_evalx.py').read().split("cols=[c for c")[0])
lvcols=[c for c in L.columns if not c.startswith('R100') and c not in('PDH_eth','PDL_eth')]
# --- confluence: count of OTHER levels within band of a level
rows=[]
for sd in fullsd:
    A=D.at[sd,'atr14']; o,h,l=S[sd]
    vals=L.loc[sd,lvcols].dropna()
    for c,v in vals.items():
        n=((vals-v).abs()<=0.05*A).sum()-1
        r,_=ev(o,h,l,v,0.10*A)
        # control: shift whole cluster by +-0.2 ATR -> same count definition but meaningless location
        cs=[ev(o,h,l,v+k*A,0.10*A)[0] for k in (-0.25,0.25)]
        rows.append((sd.year,c,n,r,np.nanmean(cs) if not all(np.isnan(cs)) else np.nan))
X=pd.DataFrame(rows,columns=['yr','lvl','n','r','ctrl'])
X['nb']=X.n.clip(upper=3)
print("hold rate by # of other levels within 0.05 ATR (R=0.1ATR):")
print(X.groupby('nb').agg(N=('r','count'),hold=('r','mean'),ctrl=('ctrl','mean')).round(3))
print(X[X.yr==2025].groupby('nb').agg(N=('r','count'),hold=('r','mean'),ctrl=('ctrl','mean')).round(3))
# --- magnet: touch prob of L vs mirror level 2*open-L (same distance, opposite side)
print("\nMagnet test: P(touch level) vs P(touch mirror level at same distance), RTH")
for c in ['PDC','PD_VWAP','PD_POC','PDH','PDL','ONH','ONL','PD_VAH','PD_VAL']:
    t=m=0;n=0
    for sd in fullsd:
        v=L.at[sd,c]; 
        if np.isnan(v): continue
        o,h,l=S[sd]; mv=2*o-v
        if abs(v-o)<0.05*D.at[sd,'atr14']: continue
        n+=1; t+= (h.max()>=v) if v>o else (l.min()<=v); m+=(h.max()>=mv) if mv>o else (l.min()<=mv)
    print(f"{c:8s} n={n} P(level)={t/n:.3f} P(mirror)={m/n:.3f} diff={(t-m)/n:+.3f}")
# --- do RTH HOD/LOD form AT levels more often than at shifted level sets?
print("\nShare of RTH HOD/LOD within 0.03 ATR of ANY reference level, real vs shifted sets:")
res={}
for k in [0,-0.3,-0.2,-0.1,0.1,0.2,0.3]:
    hit=0;n=0
    for sd in fullsd:
        A=D.at[sd,'atr14']; o,h,l=S[sd]; vals=L.loc[sd,lvcols].dropna().values+k*A
        for ext in (h.max(),l.min()):
            n+=1; hit+=(np.abs(vals-ext)<=0.03*A).any()
    res[k]=hit/n
print({k:round(v,3) for k,v in res.items()})
