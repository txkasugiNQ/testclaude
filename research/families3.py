"""Round-2 strategy classes (free RR). Each fn(params) -> trades DataFrame."""
from families2 import *
EOD=1e6
def _pack_rr(sig,d,st,rr,tb):
    R=(c[sig]-st)*d; k=(R>=0.02*A[sig])&(R<=0.6*A[sig])
    return run2(df,sig[k],d[k],st[k],rr=rr,max_bars=tb)
def _stop(mode,d,i,lvl=None):
    if mode=='sw5':  return np.where(d>0,LLV[5][i]-TICK,HHV[5][i]+TICK)
    if mode=='sw10': return np.where(d>0,LLV[10][i]-TICK,HHV[10][i]+TICK)
    if mode=='lvl':  return lvl-d*0.05*A[i]
    k=float(mode[1:]); return c[i]-d*k*A[i]
G={}
# G1 compression box, OCO stop entries at box edges
def g1(N,q,rr,tb,w):
    W=win(*WINS[w]); H=hhv(h,N); L=llv(l,N); wd=H-L
    i=np.where(W&(wd<q*A)&(wd>=0.02*A))[0]
    return run_oco(df,i,H[i]+TICK,L[i]-TICK,L[i]-TICK,H[i]+TICK,rr=rr,max_bars=tb)
G['G1_box_oco']=(g1,dict(N=[15,30,60],q=[0.05,0.08,0.12],rr=[1,2,3,EOD],tb=[0,120],w=['all','am']))
# G2 compression box, close-confirmed breakout (market next open), stop = other side / swing
def g2(N,q,stp,rr,tb,w):
    W=win(*WINS[w]); H=prev(hhv(h,N)); L=prev(llv(l,N)); wd=H-L; tight=(wd<q*A)&(wd>=0.02*A)
    up=W&tight&(c>H); dn=W&tight&(c<L)
    i=np.r_[np.where(up)[0],np.where(dn)[0]]; d=np.r_[np.ones(up.sum()),-np.ones(dn.sum())]
    st=np.where(d>0,L[i]-TICK,H[i]+TICK) if stp=='box' else _stop(stp,d,i)
    return _pack_rr(i,d,st,rr,tb)
G['G2_box_close']=(g2,dict(N=[15,30,60],q=[0.05,0.08,0.12],stp=['box','sw5'],rr=[2,3,EOD],tb=[0,120],w=['all','am']))
# G3 momentum burst with free RR / EOD / time stop
def g3(th,stp,rr,tb,w):
    s=f6(th=th,stp=stp,w=w)
    if s is None: return run2(df,[],[],[])
    return run2(df,s['sig'],s['dir'],s['stop'],rr=rr,max_bars=tb)
G['G3_burst_free']=(g3,dict(th=[0.12,0.16,0.2,0.25],stp=['sw5','sw10','k0.1'],rr=[1,2,3,EOD],tb=[0,120],w=['all','am']))
# G4 level breakout (first close beyond), continuation
PAIRS={'PD':('PDH','PDL'),'ON':('ONH','ONL'),'IB':('IBH','IBL'),'OR30':('OR30H','OR30L'),'PW':('PWH','PWL'),'LO':('LOH','LOL')}
def g4(lv,stp,rr,tb,w):
    W=win(*WINS[w]); up,dn=PAIRS[lv]
    iL=np.where(first_cross(LEV[up],1,W))[0]; iS=np.where(first_cross(LEV[dn],-1,W))[0]
    i=np.r_[iL,iS]; d=np.r_[np.ones(len(iL)),-np.ones(len(iS))]
    lvl=np.r_[LEV[up][iL],LEV[dn][iS]]
    st=_stop(stp,d,i,lvl)
    return _pack_rr(i,d,st,rr,tb)
G['G4_level_break']=(g4,dict(lv=list(PAIRS),stp=['lvl','sw5','sw10'],rr=[2,3,EOD],tb=[0,60,120],w=['all','am']))
# G5 trend-day rule: at time T, |move from RTH open| > x*A and price in outer 25% of RTH range -> follow, stop k*A
ropen=np.where(rth,pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values,np.nan)
def g5(T,x,k,rr):
    i=np.where(rth&(m==T)&~np.isnan(A))[0]; mv=(c[i]-ropen[i])/A[i]; pos=(c[i]-df.rl.values[i])/(df.rh.values[i]-df.rl.values[i])
    sel=((mv>x)&(pos>0.75))|((mv<-x)&(pos<0.25)); i=i[sel]; d=np.sign(mv[sel])
    return _pack_rr(i,d,c[i]-d*k*A[i],rr,0)
G['G5_trend_day']=(g5,dict(T=[630,660,720,780],x=[0.2,0.4],k=[0.1,0.2,0.3],rr=[2,3,EOD]))
# G6 equal highs/lows break (>=3 touches of 60-bar extreme in last 60 bars), first close beyond, once per 30 bars
H60=hhv(h,60); L60=llv(l,60)
cntH=pd.Series((h>=H60-0.02*A).astype(int)).rolling(60).sum().values; cntL=pd.Series((l<=L60+0.02*A).astype(int)).rolling(60).sum().values
def g6(nt,stp,rr,tb,w):
    W=win(*WINS[w]); up=W&(prev(cntH)>=nt)&(c>prev(H60))&(prev(c)<=prev(H60)); dn=W&(prev(cntL)>=nt)&(c<prev(L60))&(prev(c)>=prev(L60))
    i=np.r_[np.where(up)[0],np.where(dn)[0]]; d=np.r_[np.ones(up.sum()),-np.ones(dn.sum())]
    return _pack_rr(i,d,_stop(stp,d,i),rr,tb)
G['G6_equal_hl_break']=(g6,dict(nt=[3,5,8],stp=['sw5','sw10','k0.1'],rr=[2,3,EOD],tb=[0,120],w=['all','am']))
# G7 opening bar (09:30-09:31): OCO stop entries at its high/low (1-min ORB) or close-confirmed follow
ob_h=np.where(m==571,h,np.nan); ob_l=np.where(m==571,l,np.nan)
def g7(mode,k,stp,rr,tb):
    i=np.where((m==571)&~np.isnan(A))[0]
    big=np.abs(c[i]-o[i])>k*A[i]
    if mode=='oco':
        i=i[(h[i]-l[i])>=0.02*A[i]]
        exp=np.minimum(i+30,df.flat_rth.values[i])    # bracket valid 30 minutes
        if stp=='bar': return run_oco(df,i,h[i]+TICK,l[i]-TICK,l[i]-TICK,h[i]+TICK,expiry=exp,rr=rr,max_bars=tb)
        return run_oco(df,i,h[i]+TICK,h[i]-0.1*A[i],l[i]-TICK,l[i]+0.1*A[i],expiry=exp,rr=rr,max_bars=tb)
    i=i[big]; d=np.sign(c[i]-o[i])
    st=np.where(d>0,l[i]-TICK,h[i]+TICK) if stp=='bar' else c[i]-d*0.1*A[i]
    return _pack_rr(i,d,st,rr,tb)
G['G7_opening_bar']=(g7,dict(mode=['oco','close'],k=[0.0,0.03,0.06],stp=['bar','k'],rr=[1,2,3,EOD],tb=[0,30,60]))
# G8 momentum burst in overnight sessions (Asia 18:00-02:00, London 02:00-08:30), flat at RTH open-1 or time stop
ETHW={'asia':(lambda: ((m>1080)|(m<=120))&~np.isnan(A)),'london':(lambda: (m>120)&(m<=510)&~np.isnan(A))}
flat_pre=np.where(df.flat_rth.values>np.arange(len(df)),df.flat_rth.values,df.flat_eth.values)
def g8(sess,th,stp,rr,tb):
    W=ETHW[sess](); r5=RET[5]
    Lm=W&(r5>th*A)&(prev(r5)<=th*A); Sm=W&(r5<-th*A)&(prev(r5)>=-th*A)
    s=pack(Lm,Sm,stp)
    if s is None: return run2(df,[],[],[])
    return run2(df,s['sig'],s['dir'],s['stop'],rr=rr,max_bars=tb,flat=df.flat_eth.values)
G['G8_burst_overnight']=(g8,dict(sess=['asia','london'],th=[0.06,0.08,0.12,0.16],stp=['sw5','sw10'],rr=[1,2,3],tb=[60,120]))
# G9 Early Trend Ignition: momentum burst aligned with session trend, early, with range room
ropen=np.where(rth,pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values,np.nan)
RUSED=(df.rh.values-df.rl.values)/A
def g9_signals(th,ru,align,w):
    W=win(*WINS[w]); r5=RET[5]
    L_=W&(r5>th*A)&(prev(r5)<=th*A)&(RUSED<ru); S_=W&(r5<-th*A)&(prev(r5)>=-th*A)&(RUSED<ru)
    if align in ('vwap','vwap+day'): L_&=c>vrw; S_&=c<vrw
    if align=='vwap+day': L_&=c>ropen; S_&=c<ropen
    i=np.r_[np.where(L_)[0],np.where(S_)[0]]; d=np.r_[np.ones(L_.sum()),-np.ones(S_.sum())]
    o_=np.argsort(i); return i[o_],d[o_]
def g9(th,ru,align,w,ex,entry):
    i,d=g9_signals(th,ru,align,w)
    rr,tb={'rr2':(2,0),'rr3':(3,0),'eod':(EOD,0),'tb120':(EOD,120)}[ex]
    if entry=='mkt':
        st=np.where(d>0,LLV[5][i]-TICK,HHV[5][i]+TICK); return _pack_rr(i,d,st,rr,tb)
    # STOP-entry level 1 tick beyond the burst bar's 5-bar extreme, valid 5 bars; stop = other side of 5-bar range
    hi5=HHV[5][i]; lo5=LLV[5][i]; k=((hi5-lo5)>=0.02*A[i])&((hi5-lo5)<=0.6*A[i]); i,d,hi5,lo5=i[k],d[k],hi5[k],lo5[k]
    nanv=np.full(len(i),np.nan)
    pxL=np.where(d>0,hi5+TICK,np.nan); slL=np.where(d>0,lo5-TICK,np.nan)
    pxS=np.where(d<0,lo5-TICK,np.nan); slS=np.where(d<0,hi5+TICK,np.nan)
    return run_oco(df,i,pxL,slL,pxS,slS,expiry=np.minimum(i+5,df.flat_rth.values[i]),rr=rr,max_bars=tb)
WINS['to11']=(575,660); WINS['to12']=(575,720)
G['G9_early_ignition']=(g9,dict(th=[0.12,0.16],ru=[0.5,0.7,99],align=['none','vwap','vwap+day'],w=['to11','to12','all'],ex=['rr2','rr3','eod','tb120'],entry=['mkt','stop']))
G['G10_burst_level']=(g9,dict(th=[0.12,0.16,0.2],ru=[99],align=['none'],w=['all','to12'],ex=['rr2','rr3','eod','tb120'],entry=['stop','mkt']))
