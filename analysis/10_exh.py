import pandas as pd, numpy as np
df=pd.read_pickle('nq2.pkl'); D=pd.read_pickle('daily.pkl')
fullsd=D.index[(D.rn==390)&D.atr14.notna()]
G={sd:g for sd,g in df[df.sd.isin(fullsd)].groupby('sd')}
# 1) Range exhaustion: when ETH session range first reaches k*ATR, how much further does the extreme extend?
print("ETH session: when developing range first hits k*ATR -> P(new extreme extends < 0.1 ATR further), P(<0.25 ATR), median further ext (ATR), P(range reached)")
for k in [0.5,0.75,1.0,1.25,1.5,2.0]:
    ext=[];reach=0
    for sd,g in G.items():
        A=D.at[sd,'atr14']; h=g.h.values; l=g.l.values
        ch=np.maximum.accumulate(h); cl=np.minimum.accumulate(l); rg=ch-cl
        i=np.argmax(rg>=k*A)
        if rg[i]<k*A: continue
        reach+=1
        up = h[i]==ch[i]   # extreme just set on high side?
        if up: e=(h[i:].max()-ch[i])/A
        else:  e=(cl[i]-l[i:].min())/A
        ext.append(e)
    e=np.array(ext); print(f"k={k:4}: reached {reach/len(G):.2f}  P(<0.1)={np.mean(e<0.1):.2f}  P(<0.25)={np.mean(e<0.25):.2f}  med={np.median(e):.2f}")
# 2) VWAP sigma bands (RTH vwap, volume-weighted std) - first touch of +/-2 sigma after 10:00 -> revert to 1 sigma before extending 1 sigma further?
print("\nRTH VWAP band touches (after 10:00): P(return to VWAP before +1 more sigma of extension), vs control bands at 1.5/2.5 sigma")
for band in [1.0,1.5,2.0,2.5,3.0]:
    res=[]
    for sd,g in G.items():
        r=g[g.ss=='RTH']; tp=((r.h+r.l+r.c)/3).values; v=r.v.values
        cv=np.cumsum(v); vw=np.cumsum(tp*v)/cv; sd_=np.sqrt(np.maximum(np.cumsum(v*tp*tp)/cv-vw**2,0))
        h=r.h.values;l=r.l.values;mm=r['mod'].values
        for sgn in (1,-1):
            lvl=vw+sgn*band*sd_
            hit=(h>=lvl) if sgn>0 else (l<=lvl)
            hit&=(mm>600)
            if not hit.any(): continue
            t=np.argmax(hit); s=sd_[t]; L0=lvl[t]
            ext=L0+sgn*s; tgt=vw[t]
            for j in range(t+1,len(h)):
                if (sgn>0 and h[j]>=ext) or (sgn<0 and l[j]<=ext): res.append(0);break
                if (sgn>0 and l[j]<=tgt) or (sgn<0 and h[j]>=tgt): res.append(1);break
    res=np.array(res); print(f"band {band}σ: N={len(res)} P(revert to VWAP first)={res.mean():.3f}  (barrier distance ratio: ext=1σ vs back={band}σ)")
