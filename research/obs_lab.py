"""Observation lab: symmetric-barrier continuation probability after events (RW = 0.5)."""
from families2 import *
import numba as nb
flat=df.flat_rth.values; a14=df.atr14.values; YR=df.ts.dt.year.values
@nb.njit(cache=True)
def symbar(o,h,l,idx,d,s,flat,maxb):
    n=len(idx); res=np.zeros(n)   # +1 favourable first, -1 adverse first, 0 timeout/tie
    for k in range(n):
        t=idx[k]; j=t+1
        if j>flat[t]: continue
        e=o[j]; up=e+s[k]; dn=e-s[k]; end=min(flat[t],t+maxb)
        while j<=end:
            hu=h[j]>=up; hd=l[j]<=dn
            if hu and hd: break
            if hu: res[k]=d[k]; break
            if hd: res[k]=-d[k]; break
            j+=1
    return res
def pcont(idx,d,k_atr,maxb=120,years=(2023,)):
    idx=np.asarray(idx,np.int64); d=np.asarray(d,float)
    sel=np.isin(YR[idx],years)&~np.isnan(A[idx]); idx,d=idx[sel],d[sel]
    r=symbar(o,h,l,idx,d,k_atr*A[idx],flat,maxb); dec=r!=0
    n=dec.sum(); p=(r[dec]>0).mean() if n else np.nan
    return p,n,len(idx)
def z(p,n): return (p-0.5)/np.sqrt(0.25/n) if n else np.nan
W=win(575,930); body=c-o; rg=h-l
up_close=(c>prev(c)).astype(int); dn_close=(c<prev(c)).astype(int)
def runlen(x):
    s=pd.Series(x); g=(s!=s.shift()).cumsum(); return (s.groupby(g).cumcount()+1).values*x
RU_=runlen(up_close); RD_=runlen(dn_close)
H15,L15=prev(hhv(h,15)),prev(llv(l,15)); H60,L60=prev(hhv(h,60)),prev(llv(l,60)); H240,L240=prev(hhv(h,240)),prev(llv(l,240))
rh_,rl_=prev(df.rh.values),prev(df.rl.values)
ropen=np.where(rth,pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values,np.nan)
EV={}
def add(name,L_,S_): EV[name]=(np.r_[np.where(L_)[0],np.where(S_)[0]],np.r_[np.ones(L_.sum()),-np.ones(S_.sum())])
add('close breaks 15-bar extreme',W&(c>H15)&(prev(c)<=H15),W&(c<L15)&(prev(c)>=L15))
add('close breaks 60-bar extreme',W&(c>H60)&(prev(c)<=H60),W&(c<L60)&(prev(c)>=L60))
add('close breaks 240-bar extreme',W&(c>H240)&(prev(c)<=H240),W&(c<L240)&(prev(c)>=L240))
add('close makes new RTH extreme',W&(c>rh_),W&(c<rl_))
add('WICK sweep of 60-bar extreme, close back inside (fade)',W&(h>H60)&(c<H60),W&(l<L60)&(c>L60))
add('WICK sweep of RTH extreme, close back inside (fade)',W&(h>rh_)&(c<rh_),W&(l<rl_)&(c>rl_))
for lv_up,lv_dn in (('PDH','PDL'),('ONH','ONL'),('IBH','IBL')):
    add(f'close breaks {lv_up}/{lv_dn}',first_cross(LEV[lv_up],1,W),first_cross(LEV[lv_dn],-1,W))
add('shock bar |body|>3x atr14 (follow)',W&(body>3*a14),W&(body<-3*a14))
add('shock bar |body|>3x atr14 (fade)',W&(body<-3*a14),W&(body>3*a14))
add('rejection wick >2x body at new 15-bar high/low (fade)',W&(l<L15)&((np.minimum(o,c)-l)>2*np.abs(body))&(rg>1.5*a14),W&(h>H15)&((h-np.maximum(o,c))>2*np.abs(body))&(rg>1.5*a14))
add('5 consecutive closes same dir (follow)',W&(RU_==5),W&(RD_==5))
add('5 consecutive closes same dir (fade)',W&(RD_==5),W&(RU_==5))
add('close crosses VWAP (follow)',W&(c>vrw)&(prev(c)<=prev(vrw)),W&(c<vrw)&(prev(c)>=prev(vrw)))
add('price >=2σ from VWAP, first bar back inside (fade)',W&(prev(c)<prev(vrw-2*vrs))&(c>vrw-2*vrs),W&(prev(c)>prev(vrw+2*vrs))&(c<vrw+2*vrs))
mvo=(c-ropen)/A
add('far from RTH open (>0.5 ATR) -> toward open',W&(mvo<-0.5)&(prev(mvo)>=-0.5),W&(mvo>0.5)&(prev(mvo)<=0.5))
add('price re-crosses RTH open (follow cross)',W&(c>ropen)&(prev(c)<=ropen),W&(c<ropen)&(prev(c)>=ropen))
ib=(prev(h)<prev(h,2))&(prev(l)>prev(l,2))
add('1m inside-bar breakout (follow)',W&ib&(c>prev(h)),W&ib&(c<prev(l)))
eng_up=(c>o)&(prev(c)<prev(o))&(c>prev(o))&(o<prev(c))&(rg>1.5*a14); eng_dn=(c<o)&(prev(c)>prev(o))&(c<prev(o))&(o>prev(c))&(rg>1.5*a14)
add('engulfing (follow)',W&eng_up,W&eng_dn)
r5=RET[5]; add('momentum burst 0.12 ATR (follow)',W&(r5>0.12*A)&(prev(r5)<=0.12*A),W&(r5<-0.12*A)&(prev(r5)>=-0.12*A))
rows=[]
for name,(i,d) in EV.items():
    r={'event':name}
    for k in (0.03,0.06,0.12):
        p,n,N=pcont(i,d,k); r[f'p{k}']=round(p,3); r[f'z{k}']=round(z(p,n),1)
    r['N/day']=round(N/250,1); rows.append(r)
R=pd.DataFrame(rows); pd.set_option('display.width',250); print(R.to_string(index=False))
pd.to_pickle(EV,'obs_events.pkl')
