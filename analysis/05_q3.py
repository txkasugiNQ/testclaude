import pandas as pd, numpy as np
pd.set_option('display.width',200); pd.set_option('display.max_columns',30)
df=pd.read_pickle('nq2.pkl')
g=df.groupby('sd')
D=pd.DataFrame({'o':g.o.first(),'h':g.h.max(),'l':g.l.min(),'c':g.c.last(),'v':g.v.sum(),'n':g.size()})
r=df[df.ss=='RTH'].groupby('sd')
D=D.join(pd.DataFrame({'ro':r.o.first(),'rh':r.h.max(),'rl':r.l.min(),'rc':r.c.last(),'rn':r.size(),'rv':r.v.sum()}))
print("sessions with n<1300 (short/holiday):", (D.n<1300).sum(), " full RTH (390):", (D.rn==390).sum())
D['rng']=D.h-D.l; D['rrng']=D.rh-D.rl
tr=pd.concat([D.h-D.l,(D.h-D.c.shift()).abs(),(D.l-D.c.shift()).abs()],axis=1).max(axis=1)
D['atr14']=tr.rolling(14).mean().shift(1)   # known BEFORE the day
D['rng_pct']=D.rng/D.c*100
D['yr']=D.index.year
full=D[D.rn>=380]
print("\nDaily range (full ETH session) points by year:"); print(full.groupby('yr').rng.describe(percentiles=[.1,.25,.5,.75,.9]).round(1))
print("\nRTH range by year:"); print(full.groupby('yr').rrng.describe(percentiles=[.1,.5,.9]).round(1))
print("\nRange / prior ATR14 :"); x=(full.rng/full.atr14).dropna(); print(x.describe(percentiles=[.1,.25,.5,.75,.9,.95]).round(2))
print("share of ETH range covered by RTH:", (full.rrng/full.rng).median().round(3))
# volatility clustering: autocorr of daily range
print("autocorr log range lag1..5:", [round(np.log(full.rng).autocorr(k),3) for k in range(1,6)])
# NR7/inside days -> next day expansion
D['nr7']=D.rng==D.rng.rolling(7).min()
D['inside']=(D.h<D.h.shift())&(D.l>D.l.shift())
D['next_rel']=(D.rng.shift(-1)/D.atr14.shift(-1))
for k in ['nr7','inside']:
    print(k, "count",D[k].sum()," next-day range/ATR median:",D.loc[D[k],'next_rel'].median().round(3)," vs all:",D.next_rel.median().round(3))
# day of week
full2=full.assign(dow=full.index.dayofweek, rel=full.rng/full.atr14)
print("\nrange/ATR by DOW:", full2.groupby('dow').rel.median().round(3).to_dict())
# gaps RTH open vs prior RTH close
D['rgap']=D.ro-D.rc.shift()
gap=D.dropna(subset=['rgap'])
gap=gap.assign(rg_atr=gap.rgap/gap.atr14)
# gap fill same RTH: price reaches prior rc
def filled(row): pass
full3=gap[gap.rn>=380].copy()
full3['fill']=np.where(full3.rgap>0, full3.rl<=full3.rc.shift().reindex(full3.index), full3.rh>=full3.rc.shift().reindex(full3.index))
prc=D.rc.shift()
full3['fill']=np.where(full3.rgap>0, full3.rl<=prc.reindex(full3.index), full3.rh>=prc.reindex(full3.index))
full3['gbin']=pd.cut(full3.rg_atr.abs(),[0,.1,.25,.5,1,5])
print("\nRTH gap fill prob by |gap|/ATR:"); print(full3.groupby('gbin',observed=True).fill.agg(['mean','size']).round(3))
D.to_pickle('daily.pkl')
