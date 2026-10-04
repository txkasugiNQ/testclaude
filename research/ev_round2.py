from evstudy import *
rows=[]; add=lambda r: rows.append(r) if r else None
dopen=df.groupby('sd').o.transform('first').values   # session (18:00) open
ropen=pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values  # RTH open (09:30)
ropen=np.where(rth,ropen,np.nan)
sh,sl_=df.sh.values,df.sl.values; rh_,rl_=df.rh.values,df.rl.values
# A Trend-day grid: at time T, move from RTH open >= x*A and close in top/bottom 25% of RTH range -> follow to EOD
for mm in (600,630,660,720,780,840):
    i=np.where(rth&(m==mm)&~np.isnan(A))[0]
    mv=(c[i]-ropen[i])/A[i]; pos=(c[i]-rl_[i])/(rh_[i]-rl_[i])
    for x in (0.2,0.4,0.6):
        k=((mv>x)&(pos>0.75))|((mv<-x)&(pos<0.25))
        add(study(f'TREND @{mm//60}:{mm%60:02d} |mv|>{x} & at extreme',i[k],np.sign(mv[k]),hz=(30,60,120,'eod')))
# B ICT Fair Value Gap (1m, displacement): bullish if l[t]>h[t-2] and body of t-1 > 1.5*atr14; enter at close (market)
a14=df.atr14.values; body=np.abs(c-o)
bull=win(575,930)&(l>prev(h,2))&(prev(body)>1.5*prev(a14))&(prev(c)>prev(o))
bear=win(575,930)&(h<prev(l,2))&(prev(body)>1.5*prev(a14))&(prev(c)<prev(o))
add(study('FVG 1m displacement follow',np.r_[np.where(bull)[0],np.where(bear)[0]],np.r_[np.ones(bull.sum()),-np.ones(bear.sum())]))
# FVG on 5m (built from 1m at 5m boundaries)
H5,L5=hhv(h,5),llv(l,5); C5=c; O5=prev(c,5)
b5=(m%5==0)
bull5=win(575,930)&b5&(L5>prev(H5,10))&((prev(C5,5)-prev(O5,5))>0.1*A)
bear5=win(575,930)&b5&(H5<prev(L5,10))&((prev(C5,5)-prev(O5,5))<-0.1*A)
add(study('FVG 5m displacement follow',np.r_[np.where(bull5)[0],np.where(bear5)[0]],np.r_[np.ones(bull5.sum()),-np.ones(bear5.sum())]))
# C Equal highs/lows (two 15m-confirmed swing points within 0.03A in last 120 bars) -> first break: continuation
ph_=pd.Series(np.where((h==hhv(h,11))&(prev(h,5)==prev(hhv(h,11),5)),h,np.nan))
# simpler: running "double top" = current HHV60 touched twice: count bars within 0.02A of HHV60 in last 60 bars, separated
H60=hhv(h,60); L60=llv(l,60)
nearH=(h>=H60-0.02*A).astype(int); nearL=(l<=L60+0.02*A).astype(int)
cntH=pd.Series(nearH).rolling(60).sum().values; cntL=pd.Series(nearL).rolling(60).sum().values
eqh=prev(cntH)>=3; eql=prev(cntL)>=3
brkH=win(575,930)&eqh&(c>prev(H60))&(prev(c)<=prev(H60)); brkL=win(575,930)&eql&(c<prev(L60))&(prev(c)>=prev(L60))
add(study('Equal-highs/lows break follow',np.r_[np.where(brkH)[0],np.where(brkL)[0]],np.r_[np.ones(brkH.sum()),-np.ones(brkL.sum())]))
# D stale session extreme: new RTH high after >= 60 min without one -> follow
last_newh=pd.Series(np.where(rth&(h>=rh_),np.arange(len(h)),np.nan)).groupby(df.sd.values).ffill().values
last_newl=pd.Series(np.where(rth&(l<=rl_),np.arange(len(h)),np.nan)).groupby(df.sd.values).ffill().values
gapH=np.arange(len(h))-prev(last_newh); gapL=np.arange(len(h))-prev(last_newl)
for gmin in (30,60,120):
    nh=win(600,930)&(h>prev(rh_))&(gapH>=gmin); nl=win(600,930)&(l<prev(rl_))&(gapL>=gmin)
    add(study(f'stale RTH extreme break (>={gmin}m) follow',np.r_[np.where(nh)[0],np.where(nl)[0]],np.r_[np.ones(nh.sum()),-np.ones(nl.sum())]))
# E wick rejection at new RTH extreme: new high with upper wick > 60% of range and range > 2*atr14 -> fade
rg=h-l
wh=win(600,930)&(h>prev(rh_))&((h-np.maximum(o,c))>0.6*rg)&(rg>2*a14)
wl=win(600,930)&(l<prev(rl_))&((np.minimum(o,c)-l)>0.6*rg)&(rg>2*a14)
add(study('wick rejection at new extreme fade',np.r_[np.where(wh)[0],np.where(wl)[0]],np.r_[-np.ones(wh.sum()),np.ones(wl.sum())]))
# F volatility expansion: atr14/atr390 crosses above 2 -> follow direction of last 15 bars
vx=win(575,930)&(df.atr14.values/df.atr390.values>2)&(prev(df.atr14.values/df.atr390.values)<=2)
i=np.where(vx)[0]; add(study('vol expansion x2 follow 15m dir',i,np.sign(df.ret15.values[i])))
# G compression: 30-bar range < 0.1A then breakout of that box (first close beyond) -> follow
box_h=prev(hhv(h,30)); box_l=prev(llv(l,30)); tight=(box_h-box_l)<0.1*A
cb=win(575,930)&tight&(c>box_h); cs=win(575,930)&tight&(c<box_l)
add(study('compression box breakout follow',np.r_[np.where(cb)[0],np.where(cs)[0]],np.r_[np.ones(cb.sum()),-np.ones(cs.sum())]))
# H mean of session drift by entry time (unconditional long), sanity
for mm in (575,600,720,840,900):
    i=np.where(rth&(m==mm)&~np.isnan(A))[0]; add(study(f'unconditional long @{mm//60}:{mm%60:02d}',i,np.ones(len(i)),hz=(30,60,'eod')))
R=pd.DataFrame(rows); pd.set_option('display.width',250); print(R.to_string(index=False))
