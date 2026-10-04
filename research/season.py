from families2 import *
YR=df.ts.dt.year.values
# daily anchors
idx=pd.Series(np.arange(len(df)))
def at(mod): 
    i=np.where(m==mod)[0]; return pd.Series(i,index=df.sd.values[i])
i0930=at(571).groupby(level=0).first(); i1600=at(960).groupby(level=0).first(); i1801=at(1081)
first_bar=idx.groupby(df.sd.values).min()
D=pd.DataFrame({'o_rth':pd.Series(o[i0930.values],index=i0930.index),'c_rth':pd.Series(c[i1600.values],index=i1600.index),
                'o_eth':pd.Series(o[first_bar.values],index=first_bar.index)})
D['A']=pd.Series(A[first_bar.values],index=first_bar.index)
D['intraday']=(D.c_rth-D.o_rth)/D.A
D['overnight']=(D.o_rth-D.c_rth.shift())/D.A        # prior RTH close -> today's RTH open
D['yr']=D.index.year
print("S1 overnight vs intraday drift (mean in % ATR, t):")
for y,g in D.groupby('yr'):
    f=lambda x: f"{x.mean()*100:+.1f} (t={x.mean()/x.std()*np.sqrt(x.count()):.1f})"
    print(y, "overnight", f(g.overnight.dropna()), "| intraday", f(g.intraday.dropna()))
# S3 turn of month: last trading day + first 3 -> RTH open->close long, vs other days
D['dom_rank']=D.groupby(D.index.to_period('M')).cumcount(); D['dom_rev']=D.groupby(D.index.to_period('M')).cumcount(ascending=False)
tom=(D.dom_rank<=2)|(D.dom_rev==0)
for y,g in D.groupby('yr'):
    t=tom[g.index]; print(y,"TOM full-day (ovn+intraday)",round(((g.overnight+g.intraday)[t]).mean()*100,1),"vs other",round(((g.overnight+g.intraday)[~t]).mean()*100,1))
# S5 after big down/up day (intraday move < -0.8 ATR) next day intraday
D['prev_intra']=D.intraday.shift()
for y,g in D.groupby('yr'):
    print(y,"after big down day next intraday",round(g.intraday[g.prev_intra<-0.6].mean()*100,1),"n",(g.prev_intra<-0.6).sum(),
          "| after big up day",round(g.intraday[g.prev_intra>0.6].mean()*100,1),"n",(g.prev_intra>0.6).sum())
# S4 Gao intraday momentum: sign(prior close -> 10:00) predicts 15:30->16:00, all years
i1000=at(600).groupby(level=0).first(); i1530=at(930).groupby(level=0).first()
D['r_first']=(pd.Series(c[i1000.values],index=i1000.index)-D.c_rth.shift())/D.A
D['r_last']=(D.c_rth-pd.Series(c[i1530.values],index=i1530.index))/D.A
for y,g in D.groupby('yr'):
    x=np.sign(g.r_first)*g.r_last; x=x.dropna(); print(y,"Gao: sign(first)*last30",f"{x.mean()*100:+.2f} t={x.mean()/x.std()*np.sqrt(len(x)):.1f}")
# S2 half-hour slot persistence (Heston-Korajczyk-Sadka): slot return today vs mean same slot last k days
slot=((m-1)//30)                       # 30-min slot by bar start
R30=df.assign(slot=slot,r=(c-o)).groupby(['sd','slot']).r.sum().unstack()   # sum of bar (c-o) ~ slot return w/o gaps
R30=R30.div(D.A,axis=0)
rth_slots=[s for s in R30.columns if 19<=s<=31]   # 09:30..16:00
for k in (1,5,20,40):
    sig=np.sign(R30[rth_slots].rolling(k,min_periods=k).mean().shift(1))
    pnl=(sig*R30[rth_slots]); 
    for y in (2023,2024,2025):
        x=pnl[pnl.index.year==y].stack(); 
        print(f"HKS k={k} {y}: mean {x.mean()*100:+.2f}%ATR per slot-trade  t={x.mean()/x.std()*np.sqrt(len(x)):.1f} n={len(x)}")
