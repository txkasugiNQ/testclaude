import pandas as pd, numpy as np
exec(open('08_evalx.py').read().split("cols=[c for c")[0])
# Higher timeframe levels: daily swing pivots (2/2 fractal on ETH daily bars, confirmed), prior month H/L
h=D.h.values; l=D.l.values; idx=D.index
dph=pd.Series(np.nan,index=idx); dpl=pd.Series(np.nan,index=idx)
lastH=[];lastL=[]
for i in range(len(idx)):
    j=i-3   # pivot at j confirmed after bars j+1,j+2 -> usable from day j+3
    if j>=2:
        if h[j]>h[j-2:j].max() and h[j]>=h[j+1:j+3].max(): lastH.append(h[j])
        if l[j]<l[j-2:j].min() and l[j]<=l[j+1:j+3].min(): lastL.append(l[j])
    # keep unbroken pivots (not exceeded by any day up to i-1)
    if i>0:
        lastH=[x for x in lastH if x>h[i-1]]; lastL=[x for x in lastL if x<l[i-1]]
    o=D.ro.iloc[i]
    above=[x for x in lastH if x>o]; below=[x for x in lastL if x<o]
    dph.iloc[i]=min(above) if above else np.nan; dpl.iloc[i]=max(below) if below else np.nan
L['DPivH']=dph; L['DPivL']=dpl
mo=D.index.to_period('M'); M=D.groupby(mo).agg(h=('h','max'),l=('l','min')).shift()
L['PMH']=M.h.reindex(mo).values; L['PML']=M.l.reindex(mo).values
for c in ['DPivH','DPivL','PMH','PML']:
    a=run(c,0.10); b=run(c,0.20); print(c, a, "| R0.2 edge",b['edge'],"z",b['z'])
# Confluence of VWAP 2.5σ extreme with a static level
lvcols=['PDH','PDL','PDC','ONH','ONL','AsiaH','AsiaL','LonH','LonL','PWH','PWL','PD_VWAP','PD_POC','PD_VAH','PD_VAL','Piv15H','Piv15L']
G={sd:g for sd,g in df[df.sd.isin(fullsd)&(df.ss=='RTH')].groupby('sd')}
rows=[]
for sd,r in G.items():
    A=D.at[sd,'atr14']; vals=L.loc[sd,lvcols].dropna().values
    tp=((r.h+r.l+r.c)/3).values; v=r.v.values; cv=np.cumsum(v); vw=np.cumsum(tp*v)/cv
    sdv=np.sqrt(np.maximum(np.cumsum(v*tp*tp)/cv-vw**2,0)); hh=r.h.values;ll=r.l.values;mm=r['mod'].values
    for sgn in (1,-1):
        lvl=vw+sgn*2.0*sdv; hit=((hh>=lvl) if sgn>0 else (ll<=lvl))&(mm>600)
        if not hit.any(): continue
        t=np.argmax(hit); px=lvl[t]; conf=(np.abs(vals-px)<=0.1*A).any(); ext=px+sgn*sdv[t]; tgt=vw[t]
        for j in range(t+1,len(hh)):
            if (sgn>0 and hh[j]>=ext) or (sgn<0 and ll[j]<=ext): rows.append((conf,0));break
            if (sgn>0 and ll[j]<=tgt) or (sgn<0 and hh[j]>=tgt): rows.append((conf,1));break
X=pd.DataFrame(rows,columns=['conf','rev']); print("\nVWAP 2σ touch, with/without static level within 0.1ATR (baseline .333):"); print(X.groupby('conf').rev.agg(['size','mean']).round(3))
# hold rate by time of first touch for all static levels pooled
