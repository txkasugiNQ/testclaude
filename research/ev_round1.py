from evstudy import *
W=win(575,930); rows=[]
add=lambda r: rows.append(r) if r else None
# 1 level breaks (first close beyond), continuation direction
for up,dn in zip(UPPER,LOWER):
    iL=np.where(first_cross(LEV[up],1,W))[0]; iS=np.where(first_cross(LEV[dn],-1,W))[0]
    add(study(f'break {up}/{dn}',np.r_[iL,iS],np.r_[np.ones(len(iL)),-np.ones(len(iS))]))
# 2 momentum bursts
for th in (0.08,0.12,0.16,0.25):
    s=f6(th=th,stp='k0.1',w='all'); add(study(f'burst {th}',s['sig'],s['dir']))
# 3 opening drive: return 09:30->09:45 / 10:00 sign, enter at that time
for mm,lab in ((585,'OD15'),(600,'OD30'),(630,'OD60')):
    i=np.where(rth&(m==mm)&~np.isnan(A))[0]; op=df.groupby('sd').o.transform(lambda x:x.iloc[0]).values
    r0=np.array([c[k]-o[k-(mm-570)+1] for k in i]); add(study(f'{lab} follow',i,np.sign(r0)))
    big=np.abs(r0)>0.15*A[i]; add(study(f'{lab} follow |r|>0.15A',i[big],np.sign(r0[big])))
# 4 gap direction at 09:31 bar (gap = open09:30 - prior RTH close), follow vs fade
i=np.where(rth&(m==571)&~np.isnan(A))[0]; g=(o[i]-pcl[i])/A[i]
for lo_,hi_ in ((0.1,0.3),(0.3,0.6),(0.6,9)):
    k=(np.abs(g)>lo_)&(np.abs(g)<=hi_); add(study(f'gap follow {lo_}-{hi_}',i[k],np.sign(g[k])))
# 5 intraday momentum (Gao et al.): sign of (prior close -> 10:00) predicts last 30 min; enter 15:30
day_first=pd.Series(np.arange(len(df))).groupby(df.sd.values).transform('min').values
i30=np.where(rth&(m==930)&~np.isnan(A))[0]
sd_to_10={}
idx10=np.where(rth&(m==600))[0]; s10=pd.Series(c[idx10],index=df.sd.values[idx10])
r_am=(s10.reindex(df.sd.values[i30]).values-pcl[i30])
k=~np.isnan(r_am); add(study('IntradayMom: sign(pclose->10:00) @15:30',i30[k],np.sign(r_am[k]),hz=(15,30,'eod')))
r_day=c[i30]-df.groupby('sd').o.transform('first').values[i30]
add(study('IntradayMom: sign(open->15:30) @15:30',i30,np.sign(r_day),hz=(15,30,'eod')))
# 6 position in day range at fixed times -> drift to close
for mm in (630,720,840):
    i=np.where(rth&(m==mm)&~np.isnan(A))[0]; pos=(c[i]-df.sl.values[i])/(df.sh.values[i]-df.sl.values[i])
    k=pos>0.85; add(study(f'near session high @{mm//60}:{mm%60:02d} -> long',i[k],np.ones(k.sum()),hz=(30,60,'eod')))
    k=pos<0.15; add(study(f'near session low @{mm//60}:{mm%60:02d} -> short',i[k],-np.ones(k.sum()),hz=(30,60,'eod')))
# 7 VWAP extreme touches (first per day after 10:00) -> fade
for b in (2,2.5,3):
    L_=once_per_day(win(600,930)&(l<=vrw-b*vrs)); S_=once_per_day(win(600,930)&(h>=vrw+b*vrs))
    iL=np.where(L_)[0]; iS=np.where(S_)[0]; add(study(f'VWAP {b}σ touch fade',np.r_[iL,iS],np.r_[np.ones(len(iL)),-np.ones(len(iS))]))
# 8 sweep & reclaim of PDH/PDL/ONH/ONL (trade beyond then close back inside within 5 bars) -> fade
for up,dn in (('PDH','PDL'),('ONH','ONL'),('IBH','IBL'),('LOH','LOL')):
    Lv=LEV[up]; poke=W&(HHV[5]>Lv)&(c<Lv)&(prev(c)>=Lv); iS=np.where(once_per_day(poke))[0]
    Lv2=LEV[dn]; poke2=W&(LLV[5]<Lv2)&(c>Lv2)&(prev(c)<=Lv2); iL=np.where(once_per_day(poke2))[0]
    add(study(f'sweep-reclaim fade {up}/{dn}',np.r_[iL,iS],np.r_[np.ones(len(iL)),-np.ones(len(iS))]))
R=pd.DataFrame(rows); pd.set_option('display.width',250); print(R.to_string(index=False))
