import pandas as pd, numpy as np
df=pd.read_pickle('nq2.pkl'); D=pd.read_pickle('daily.pkl')
fullsd=D.index[(D.rn==390)&D.atr14.notna()]
# ---------- build reference levels per session, ONLY from info available before use ----------
L=pd.DataFrame(index=D.index)
L['PDH']=D.rh.shift(); L['PDL']=D.rl.shift(); L['PDC']=D.rc.shift()
L['PDH_eth']=D.h.shift(); L['PDL_eth']=D.l.shift()
on=df[df.ss.isin(['ASIA','LON','PRE'])].groupby('sd').agg(h=('h','max'),l=('l','min'))
L['ONH']=on.h; L['ONL']=on.l
a=df[df.ss=='ASIA'].groupby('sd').agg(h=('h','max'),l=('l','min')); L['AsiaH']=a.h; L['AsiaL']=a.l
lo=df[df.ss=='LON'].groupby('sd').agg(h=('h','max'),l=('l','min')); L['LonH']=lo.h; L['LonL']=lo.l
# prior week (by ISO week of session date) RTH-agnostic full H/L
wk=D.index.to_period('W-FRI'); W=D.groupby(wk).agg(h=('h','max'),l=('l','min')).shift()
L['PWH']=W.h.reindex(wk).values; L['PWL']=W.l.reindex(wk).values
# prior RTH session settle VWAP (vwap at 16:00)
vw=df[(df['mod']==960)].set_index('sd').vr; L['PD_VWAP']=vw.shift().reindex(L.index)
# prior day volume profile POC/VAH/VAL from RTH bars
R=df[df.ss=='RTH']
poc={};vah={};val={}
for sd,g in R.groupby('sd'):
    lo_=g.l.min(); n=int(round((g.h.max()-lo_)*4))+1; vol=np.zeros(n)
    li=np.round((g.l.values-lo_)*4).astype(int); hi=np.round((g.h.values-lo_)*4).astype(int)
    for a_,b_,v_ in zip(li,hi,g.v.values): vol[a_:b_+1]+=v_/(b_-a_+1)
    p=vol.argmax(); tot=vol.sum(); s=vol[p]; i=j=p
    while s<0.7*tot:
        up=vol[j+1] if j+1<n else -1; dn=vol[i-1] if i>0 else -1
        if up>=dn: j+=1; s+=up
        else: i-=1; s+=dn
    poc[sd]=lo_+p/4; vah[sd]=lo_+j/4; val[sd]=lo_+i/4
L['PD_POC']=pd.Series(poc).shift().reindex(L.index); L['PD_VAH']=pd.Series(vah).shift().reindex(L.index); L['PD_VAL']=pd.Series(val).shift().reindex(L.index)
# swing pivots on 15m bars (confirmed 5 bars later), nearest UNBROKEN pivot above/below RTH open
b15=df.set_index('ts')[['o','h','l','c']].resample('15min',label='right',closed='right').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
k=5; H=b15.h.values; Lo=b15.l.values; t=b15.index
ph=[(t[i+k],H[i]) for i in range(k,len(H)-k) if H[i]==H[i-k:i+k+1].max() and (H[i-k:i]<H[i]).all()]
pl=[(t[i+k],Lo[i]) for i in range(k,len(Lo)-k) if Lo[i]==Lo[i-k:i+k+1].min() and (Lo[i-k:i]>Lo[i]).all()]
# for unbroken check need running max/min after confirmation until session's RTH open
dfi=df.set_index('ts'); hs=dfi.h; ls=dfi.l
import bisect
ts_arr=df.ts.values; hh=df.h.values; ll=df.l.values
# prefix structures: use sparse approach — for each pivot compute first break time
def first_break(conf_t, lvl, arr, up):
    i=np.searchsorted(ts_arr, np.datetime64(conf_t), side='right')
    seg=arr[i:]
    idx=np.argmax(seg>lvl) if up else np.argmax(seg<lvl)
    ok=(seg[idx]>lvl) if up else (seg[idx]<lvl)
    return ts_arr[i+idx] if ok else np.datetime64('2100-01-01')
# vectorised-ish: chunked to limit cost
phb=[(c,v,first_break(c,v,hh,True)) for c,v in ph]; plb=[(c,v,first_break(c,v,ll,False)) for c,v in pl]
print("pivots",len(phb),len(plb))
rth_open={sd:np.datetime64(sd+pd.Timedelta(minutes=570)) for sd in D.index}
ro=D.ro
P_H={};P_L={}
phA=pd.DataFrame(phb,columns=['c','v','b']); plA=pd.DataFrame(plb,columns=['c','v','b'])
for sd in D.index:
    t0=sd+pd.Timedelta(minutes=570)
    x=phA[(phA.c<=t0)&(phA.b>t0)&(phA.v>ro[sd])]; P_H[sd]=x.v.min() if len(x) else np.nan
    y=plA[(plA.c<=t0)&(plA.b>t0)&(plA.v<ro[sd])]; P_L[sd]=y.v.max() if len(y) else np.nan
L['Piv15H']=pd.Series(P_H); L['Piv15L']=pd.Series(P_L)
# Placebo: round numbers (prices are back-adjusted -> historical "round" numbers are not real round numbers)
L['R100_up']=np.ceil(D.ro/100)*100; L['R100_dn']=np.floor(D.ro/100)*100
L.to_pickle('levels.pkl'); print(L.dropna().tail(3).T)
