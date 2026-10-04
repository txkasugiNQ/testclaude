import pandas as pd, numpy as np
df=pd.read_pickle('nq2.pkl'); D=pd.read_pickle('daily.pkl'); L=pd.read_pickle('levels.pkl')
fullsd=D.index[(D.rn==390)&D.atr14.notna()]
R=df[(df.ss=='RTH')&df.sd.isin(fullsd)]
S={sd:(g.o.values,g.h.values,g.l.values,g.c.values) for sd,g in R.groupby('sd')}
lvcols=['PDH','PDL','PDC','ONH','ONL','AsiaH','AsiaL','LonH','LonL','PWH','PWL','PD_VWAP','PD_POC','PD_VAH','PD_VAL','Piv15H','Piv15L']
def sweep(o,h,l,c,lvl,A,N=10):
    """resistance case if lvl>open: trade above lvl by >=0.02A, then close back below lvl within N bars.
       entry=close of reclaim bar, stop=sweep extreme, target=entry-1R. returns 1 win,0 loss,nan none"""
    res_side = lvl>o[0]
    if res_side: br=np.where(h>=lvl+0.02*A)[0]
    else: br=np.where(l<=lvl-0.02*A)[0]
    if len(br)==0: return np.nan
    t=br[0]
    for j in range(t,min(t+N,len(c))):
        if (res_side and c[j]<lvl) or ((not res_side) and c[j]>lvl):
            ext=h[t:j+1].max() if res_side else l[t:j+1].min()
            risk=abs(ext-c[j]); 
            if risk<0.02*A: return np.nan
            tgt=c[j]-risk if res_side else c[j]+risk
            for k in range(j+1,len(c)):
                hs = h[k]>=ext if res_side else l[k]<=ext
                ht = l[k]<=tgt if res_side else h[k]>=tgt
                if hs: return 0.0
                if ht: return 1.0
            return np.nan
    return np.nan
rows=[]
for sd in fullsd:
    o,h,l,c=S[sd]; A=D.at[sd,'atr14']
    for col in lvcols:
        v=L.at[sd,col]
        if np.isnan(v): continue
        r=sweep(o,h,l,c,v,A)
        cs=[sweep(o,h,l,c,v+k*A,A) for k in (-0.3,-0.2,0.2,0.3)]
        rows.append((sd.year,col,r,np.nanmean(cs) if not np.all(np.isnan(cs)) else np.nan))
X=pd.DataFrame(rows,columns=['yr','lvl','r','ctrl'])
print("Sweep&Reclaim 1R:1R, win rate. RW baseline ~0.5")
print("ALL real:",round(X.r.mean(),3),"N",X.r.count()," control:",round(X.ctrl.mean(),3))
print(X.groupby('lvl').agg(N=('r','count'),win=('r','mean'),ctrl=('ctrl','mean')).round(3).sort_values('win',ascending=False).to_string())
print(X.groupby('yr').agg(N=('r','count'),win=('r','mean'),ctrl=('ctrl','mean')).round(3))
