"""Rule-based setup families. Every signal uses only information up to the CLOSE of bar t.
Each generator returns dict(sig, dir, stop, [etype, epx, expiry]) ; params -> name."""
from feats import *
import itertools
df=build()
o,h,l,c=[df[k].values for k in 'ohlc']; m=df['mod'].values; A=df.atrD.values; rth=df.rth.values
sd_codes=pd.factorize(df.sd)[0]
def llv(x,n): return pd.Series(x).rolling(n).min().values
def hhv(x,n): return pd.Series(x).rolling(n).max().values
LLV={n:llv(l,n) for n in (3,5,10,20,30)}; HHV={n:hhv(h,n) for n in (3,5,10,20,30)}
first_of_day=np.r_[True,sd_codes[1:]!=sd_codes[:-1]]
def prev(x,k=1): return np.r_[np.full(k,np.nan),x[:-k]]
def win(a,b): return rth&(m>a)&(m<=b)&~np.isnan(A)
WINS={'all':(575,930),'am':(575,690),'mid':(690,840),'pm':(840,930)}
def once_per_day(mask):
    """keep only first True per session"""
    idx=np.where(mask)[0]; _,f=np.unique(sd_codes[idx],return_index=True); out=np.zeros_like(mask); out[idx[f]]=True; return out
def stop_from(mode,d,i):
    if mode.startswith('sw'):   # swing stop over N bars
        n=int(mode[2:]); return (LLV[n][i]-TICK) if d>0 else (HHV[n][i]+TICK)
    k=float(mode[1:]); return c[i]-d*k*A[i]           # fixed fraction of daily ATR
def pack(longm,shortm,stopmode,minR=0.03,maxR=0.4):
    out=[]
    for d,mask in ((1,longm),(-1,shortm)):
        i=np.where(mask)[0]
        if len(i)==0: continue
        st=stop_from(stopmode,d,i); R=(c[i]-st)*d
        ok=(R>=minR*A[i])&(R<=maxR*A[i])
        out.append((i[ok],np.full(ok.sum(),d),st[ok]))
    if not out: return None
    s=np.concatenate([x[0] for x in out]); dd=np.concatenate([x[1] for x in out]); st=np.concatenate([x[2] for x in out])
    return dict(sig=s,dir=dd,stop=st)
vrw,vrs=df.vrw.values,df.vrs.values
e={n:df[f'ema{n}'].values for n in (9,21,50,100,200,500)}
FAM={}
# F1 VWAP sigma-band re-entry (mean reversion)
def f1(b,stp,w):
    W=win(*WINS[w]); lo=vrw-b*vrs; hi=vrw+b*vrs
    L=W&(prev(c)<prev(lo))&(c>lo); S=W&(prev(c)>prev(hi))&(c<hi)
    return pack(L,S,stp)
FAM['F1_vwap_reentry']=(f1,dict(b=[1.5,2,2.5,3],stp=['sw10','sw20','k0.05','k0.1'],w=list(WINS)))
# F2 trend pullback to MA / VWAP, resume candle
def f2(ref,tf,stp,w):
    W=win(*WINS[w]); r={'e21':e[21],'e50':e[50],'vwap':vrw}[ref]
    up=(e[50]>e[200])&(c>vrw) if tf=='ema' else (c>vrw)&(e[21]>e[50])
    dn=(e[50]<e[200])&(c<vrw) if tf=='ema' else (c<vrw)&(e[21]<e[50])
    L=W&up&(l<=r)&(c>r)&(c>o); S=W&dn&(h>=r)&(c<r)&(c<o)
    return pack(L,S,stp)
FAM['F2_trend_pullback']=(f2,dict(ref=['e21','e50','vwap'],tf=['ema','fast'],stp=['sw5','sw10','k0.05','k0.1'],w=list(WINS)))
# F3 opening range breakout (first close beyond, once per day per side)
orH={15:df.or15h.values,30:df.or30h.values,60:df.ibh.values}; orL={15:df.or15l.values,30:df.or30l.values,60:df.ibl.values}
def f3(n,stp,lastm):
    W=rth&(m<=lastm)&~np.isnan(orH[n])
    L=once_per_day(W&(c>orH[n])&(prev(c)<=orH[n])); S=once_per_day(W&(c<orL[n])&(prev(c)>=orL[n]))
    if stp=='mid':
        out=[]
        for d,mask in ((1,L),(-1,S)):
            i=np.where(mask)[0]; st=(orH[n][i]+orL[n][i])/2; out.append((i,np.full(len(i),d),st))
        s=np.concatenate([x[0] for x in out]); return dict(sig=s,dir=np.concatenate([x[1] for x in out]),stop=np.concatenate([x[2] for x in out]))
    return pack(L,S,stp,maxR=0.6)
FAM['F3_ORB']=(f3,dict(n=[15,30,60],stp=['mid','sw10','k0.1','k0.2'],lastm=[660,750,900]))
# F4 opening range fade: poke beyond OR then close back inside
def f4(n,stp,lastm):
    W=rth&(m<=lastm)&~np.isnan(orH[n])
    S=once_per_day(W&(HHV[5]>orH[n])&(c<orH[n])&(prev(c)>=orH[n])); L=once_per_day(W&(LLV[5]<orL[n])&(c>orL[n])&(prev(c)<=orL[n]))
    return pack(L,S,stp)
FAM['F4_OR_fade']=(f4,dict(n=[15,30,60],stp=['sw5','sw10','k0.05','k0.1'],lastm=[750,900]))
# F5 RSI extreme with trend filter, entry on cross back
rs=df.rsi14.values
def f5(lo,tf,stp,w):
    W=win(*WINS[w]); up=c>e[200] if tf else np.ones(len(c),bool); dn=c<e[200] if tf else np.ones(len(c),bool)
    L=W&up&(prev(rs)<lo)&(rs>=lo); S=W&dn&(prev(rs)>100-lo)&(rs<=100-lo)
    return pack(L,S,stp)
FAM['F5_RSI_extreme']=(f5,dict(lo=[15,20,25,30],tf=[True,False],stp=['sw10','sw20','k0.05','k0.1'],w=list(WINS)))
# F6 momentum burst continuation
r5=df.ret5.values
def f6(th,stp,w):
    W=win(*WINS[w]); L=W&(r5>th*A)&(prev(r5)<=th*A); S=W&(r5<-th*A)&(prev(r5)>=-th*A)
    return pack(L,S,stp)
FAM['F6_mom_burst']=(f6,dict(th=[0.05,0.08,0.12,0.16],stp=['sw5','sw10','k0.05','k0.1'],w=list(WINS)))
# F7 N consecutive counter-trend closes in trend -> buy dip
dnb=(c<prev(c)).astype(int); upb=(c>prev(c)).astype(int)
def runlen(x):
    s=pd.Series(x); g=(s!=s.shift()).cumsum(); return (s.groupby(g).cumcount()+1).values*x
RD=runlen(dnb); RU=runlen(upb)
def f7(n,stp,w):
    W=win(*WINS[w]); up=(e[50]>e[200]); dn=(e[50]<e[200])
    L=W&up&(prev(RD)>=n)&(c>prev(c)); S=W&dn&(prev(RU)>=n)&(c<prev(c))
    return pack(L,S,stp)
FAM['F7_consec_dip']=(f7,dict(n=[3,4,5,6],stp=['sw5','sw10','k0.05','k0.1'],w=list(WINS)))
# F8 quiet-day fade of new session extremes
rh,rl=df.rh.values,df.rl.values
def f8(ru,stp,w):
    W=win(*WINS[w])&((rh-rl)<ru*A)
    S=W&(h>=rh)&(prev(rh)<rh)&(c<h); L=W&(l<=rl)&(prev(rl)>rl)&(c>l)
    return pack(L,S,stp)
FAM['F8_quiet_fade']=(f8,dict(ru=[0.4,0.6,0.8,1.0],stp=['k0.05','k0.1','k0.15','sw10'],w=['all','mid','pm']))
# F9 gap fill toward prior close (decided at 09:31 bar)
pcl=df.pcl.values
def f9(g1,g2,k):
    first=rth&(m==571)&~np.isnan(A)
    gap=(c-pcl)/A
    L=first&(gap<-g1)&(gap>-g2); S=first&(gap>g1)&(gap<g2)
    return pack(L,S,f'k{k}',maxR=0.6)
FAM['F9_gap_fill']=(f9,dict(g1=[0.05,0.1,0.2],g2=[0.3,0.5,1.0],k=[0.1,0.2,0.3]))
# F11 z-score reversion in low-vol regime
z60=df.z60.values; vr=df.atr60.values/df.atr390.values
def f11(z,vmax,stp,w):
    W=win(*WINS[w])&(vr<vmax)
    L=W&(prev(z60)<-z)&(z60>=-z); S=W&(prev(z60)>z)&(z60<=z)
    return pack(L,S,stp)
FAM['F11_z_lowvol']=(f11,dict(z=[2,2.5,3],vmax=[0.8,1.0,1.5,99],stp=['sw10','sw20','k0.05','k0.1'],w=list(WINS)))
# F12 time-of-day drift (fixed minute, fixed direction)
def f12(mm,d,k):
    W=rth&(m==mm)&~np.isnan(A)
    return pack(W if d>0 else np.zeros_like(W),W if d<0 else np.zeros_like(W),f'k{k}',maxR=0.6)
FAM['F12_time_drift']=(f12,dict(mm=list(range(600,931,30)),d=[1,-1],k=[0.05,0.1,0.2]))
# F13 limit order at levels (anticipatable): buy limit at prior-day low / VWAP-2sigma etc., stop k*A beyond
pl,ph=df.pl.values,df.ph.values
def f13(lvl,k,w):
    a,b=WINS[w]; W=win(a,b)
    # signal at bar where level is defined & price on correct side; one order per day per side, expires at window end
    if lvl=='pd':   Lp,Sp=pl,ph
    elif lvl=='or': Lp,Sp=orL[30],orH[30]
    elif lvl=='v2': Lp,Sp=vrw-2*vrs,vrw+2*vrs
    else:           Lp,Sp=vrw-3*vrs,vrw+3*vrs
    sig=[];dd=[];st=[];epx=[];exp=[]
    endidx=df.flat_rth.values
    for d,P in ((1,Lp),(-1,Sp)):
        cond=W&~np.isnan(P)&((c>P+0.05*A) if d>0 else (c<P-0.05*A))
        i=np.where(once_per_day(cond))[0]
        sig.append(i); dd.append(np.full(len(i),d)); epx.append(P[i]); st.append(P[i]-d*k*A[i]); exp.append(endidx[i])
    return dict(sig=np.concatenate(sig),dir=np.concatenate(dd),stop=np.concatenate(st),etype=np.ones(sum(len(x) for x in sig),np.int64),epx=np.concatenate(epx),expiry=np.concatenate(exp))
FAM['F13_limit_levels']=(f13,dict(lvl=['pd','or','v2','v3'],k=[0.05,0.1,0.15,0.2],w=['all','am']))
# F6b refined momentum burst: lookback, trend alignment, volume, time, stop
vol=df.v.values; vrel=pd.Series(vol).rolling(5).mean().values/pd.Series(vol).rolling(390).mean().values
RET={n:c-prev(c,n) for n in (3,5,10)}
def f6b(n,th,tf,vf,stp,w):
    W=win(*WINS[w]); r=RET[n]
    if tf=='none': up=dn=np.ones(len(c),bool)
    elif tf=='vwap': up=c>vrw; dn=c<vrw
    else: up=(e[50]>e[200])&(c>vrw); dn=(e[50]<e[200])&(c<vrw)
    V=vrel>vf
    L=W&up&V&(r>th*A)&(prev(r)<=th*A); S=W&dn&V&(r<-th*A)&(prev(r)>=-th*A)
    return pack(L,S,stp)
FAM['F6b_mom_refined']=(f6b,dict(n=[3,5,10],th=[0.05,0.08,0.12,0.16],tf=['none','vwap','ema'],vf=[0,1.5],stp=['sw5','sw10','k0.05','k0.1'],w=['all','am','mid','pm']))
# daily regime (known before session): prior RTH close vs 20-day SMA of closes
_dc=df[rth].groupby('sd').c.last(); _reg=(_dc>_dc.rolling(20).mean()).shift(1)
REG=df.sd.map(_reg).values.astype(float)   # 1 bull, 0 bear, nan unknown
# F14 impulse -> retracement LIMIT (anticipatable: level known before fill)
def f14(n,th,ret,kst,tf,w):
    W=win(*WINS[w]); r=RET[n]
    up=np.ones(len(c),bool) if tf=='none' else (REG==1); dn=np.ones(len(c),bool) if tf=='none' else (REG==0)
    sig=[];dd=[];st=[];epx=[];exp=[]
    for d in (1,-1):
        if d>0: cond=W&up&(r>th*A)&(prev(r)<=th*A); lo_=LLV[10]; hi_=HHV[10]
        else:   cond=W&dn&(r<-th*A)&(prev(r)>=-th*A); lo_=LLV[10]; hi_=HHV[10]
        i=np.where(cond)[0]
        if d>0: base=lo_[i]; top=hi_[i]; P=top-ret*(top-base); S=base-kst*A[i]
        else:   base=hi_[i]; top=lo_[i]; P=top+ret*(base-top); S=base+kst*A[i]
        okk=((P-S)*d>=0.03*A[i])
        i,P,S=i[okk],P[okk],S[okk]
        sig.append(i); dd.append(np.full(len(i),d)); epx.append(P); st.append(S); exp.append(np.minimum(i+30,df.flat_rth.values[i]))
    return dict(sig=np.concatenate(sig),dir=np.concatenate(dd),stop=np.concatenate(st),etype=np.ones(sum(len(x) for x in sig),np.int64),epx=np.concatenate(epx),expiry=np.concatenate(exp))
FAM['F14_impulse_retrace_limit']=(f14,dict(n=[5,10],th=[0.08,0.12,0.16],ret=[0.382,0.5,0.618],kst=[0.0,0.02],tf=['none','reg'],w=['all','am']))
# F15 break & retest of OR30/IB/prior-day level: after first close beyond, limit at level, stop k*A beyond
def f15(lv,k,w):
    a,b=WINS[w]; W=win(a,b)
    Hs={'or30':orH[30],'ib':orH[60],'pd':ph}[lv]; Ls={'or30':orL[30],'ib':orL[60],'pd':pl}[lv]
    sig=[];dd=[];st=[];epx=[];exp=[]
    for d,P in ((1,Hs),(-1,Ls)):
        cond=W&~np.isnan(P)&(((c>P)&(prev(c)<=P)) if d>0 else ((c<P)&(prev(c)>=P)))
        i=np.where(once_per_day(cond))[0]
        sig.append(i); dd.append(np.full(len(i),d)); epx.append(P[i]); st.append(P[i]-d*k*A[i]); exp.append(df.flat_rth.values[i])
    return dict(sig=np.concatenate(sig),dir=np.concatenate(dd),stop=np.concatenate(st),etype=np.ones(sum(len(x) for x in sig),np.int64),epx=np.concatenate(epx),expiry=np.concatenate(exp))
FAM['F15_break_retest']=(f15,dict(lv=['or30','ib','pd'],k=[0.05,0.1,0.15,0.2],w=['all','am']))
# F16 HTF bull/bear regime + intraday pullback to VWAP / VWAP-1sigma, market entry on reclaim
def f16(band,stp,w):
    W=win(*WINS[w]); lo=vrw-band*vrs; hi=vrw+band*vrs
    L=W&(REG==1)&(prev(l)<=prev(lo))&(c>lo)&(c>o); S=W&(REG==0)&(prev(h)>=prev(hi))&(c<hi)&(c<o)
    return pack(L,S,stp)
FAM['F16_regime_vwap_dip']=(f16,dict(band=[0,0.5,1,1.5,2],stp=['sw5','sw10','k0.05','k0.1'],w=list(WINS)))
VR=df.atr60.values/df.atr390.values; RU=(df.sh.values-df.sl.values)/A
def f14b(n,th,ret,tf,rumin,vrmax):
    s=f14(n=n,th=th,ret=ret,kst=0.0,tf=tf,w='all')
    i=s['sig']; keep=(RU[i]>rumin)&(VR[i]<vrmax)
    return {k:(v[keep] if hasattr(v,'__len__') else v) for k,v in s.items()}
FAM['F14b_retrace_filtered']=(f14b,dict(n=[5,10,20] if False else [5,10],th=[0.08,0.12],ret=[0.382,0.5,0.618],tf=['none','reg'],rumin=[0,0.5,0.8],vrmax=[99,1.2,1.0,0.8]))
# F17 capitulation bar fade: 1-min range > x * atr390 against the trend of last 30 bars, enter reversal on next bar
a390=df.atr390.values; rng1=h-l
def f17(x,stp,w):
    W=win(*WINS[w])
    big=rng1>x*a390
    L=W&big&(c<o)&(c>l+0.3*rng1)   # big red bar closing off the low (wick)
    S=W&big&(c>o)&(c<h-0.3*rng1)
    return pack(L,S,stp)
FAM['F17_capitulation']=(f17,dict(x=[3,4,5,6],stp=['sw3','sw5','k0.05','k0.1'],w=list(WINS)))
# F18 VWAP 3-sigma limit reversion (anticipatable), stop k*A beyond, valid until window end
def f18(b,k,w):
    a,bb=WINS[w]; W=win(a,bb); sig=[];dd=[];st=[];epx=[];exp=[]
    for d,P in ((1,vrw-b*vrs),(-1,vrw+b*vrs)):
        cond=W&~np.isnan(P)&(((c>P)&(l>P)) if d>0 else ((c<P)&(h<P)))&(m>=600)
        i=np.where(cond)[0]
        sig.append(i); dd.append(np.full(len(i),d)); epx.append(P[i]); st.append(P[i]-d*k*A[i]); exp.append(np.minimum(i+1,df.flat_rth.values[i]))
    # re-quoted every bar (order refreshed each minute at the current band) -> expiry = next bar
    return dict(sig=np.concatenate(sig),dir=np.concatenate(dd),stop=np.concatenate(st),etype=np.ones(sum(len(x) for x in sig),np.int64),epx=np.concatenate(epx),expiry=np.concatenate(exp))
FAM['F18_vwap_band_limit']=(f18,dict(b=[2,2.5,3,3.5],k=[0.05,0.1,0.15],w=['all','am','mid','pm']))
# F19 trend day: after IB, price > IB high + x*IBwidth -> buy pullback to EMA21 (reclaim)
def f19(x,stp,w):
    W=win(*WINS[w])&~np.isnan(orH[60]); ibw=orH[60]-orL[60]
    up=HHV[30]>orH[60]+x*ibw; dn=LLV[30]<orL[60]-x*ibw
    L=W&up&(c>orH[60])&(l<=e[21])&(c>e[21]); S=W&dn&(c<orL[60])&(h>=e[21])&(c<e[21])
    return pack(L,S,stp)
FAM['F19_trendday_pullback']=(f19,dict(x=[0.25,0.5,1.0],stp=['sw5','sw10','k0.05','k0.1'],w=['mid','pm','all']))
# F20 5-minute inside bar breakout (5m bars built causally from 1m: valid at 5m boundaries)
b5=(m%5==0)
H5=hhv(h,5); L5=llv(l,5)
def f20(stp,tf,w):
    W=win(*WINS[w])&b5
    pH=prev(H5,5); pL=prev(L5,5); ppH=prev(H5,10); ppL=prev(L5,10)
    inside=(pH<ppH)&(pL>ppL)
    up=np.ones(len(c),bool) if tf=='none' else (c>vrw); dn=np.ones(len(c),bool) if tf=='none' else (c<vrw)
    L=W&inside&up&(c>pH); S=W&inside&dn&(c<pL)
    return pack(L,S,stp)
FAM['F20_inside5m_breakout']=(f20,dict(stp=['sw5','sw10','k0.05','k0.1'],tf=['none','vwap'],w=list(WINS)))
# F21 pre-market (08:30-09:30) range breakout after 09:30, once per day per side
pre=(m>510)&(m<=570); key=df.sd.values
PH=pd.Series(np.where(pre,h,np.nan)).groupby(key).transform('max').values; PL=pd.Series(np.where(pre,l,np.nan)).groupby(key).transform('min').values
def f21(stp,lastm):
    W=rth&(m<=lastm)&~np.isnan(A)
    L=once_per_day(W&(c>PH)&(prev(c)<=PH)); S=once_per_day(W&(c<PL)&(prev(c)>=PL))
    return pack(L,S,stp,maxR=0.6)
FAM['F21_premarket_breakout']=(f21,dict(stp=['sw5','sw10','k0.1','k0.2'],lastm=[630,690,900]))
