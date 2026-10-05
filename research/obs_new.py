from obs_lab import *
vol=df.v.values.astype(float)
# time-of-day normalised volume: bar volume / mean volume of same minute over prior 20 sessions (causal)
tod=df['mod'].values
vt=pd.DataFrame({'sd':df.sd.values,'mod':tod,'v':vol})
piv=vt.pivot_table(index='sd',columns='mod',values='v',aggfunc='sum')
base=piv.rolling(20,min_periods=10).mean().shift(1)
bv=base.stack().rename('b').reset_index()
vt=vt.merge(bv,on=['sd','mod'],how='left'); RV=(vt.v/vt.b).values
print("== (a) volume as order-flow proxy (2023, p at symmetric barriers) ==")
rows=[]
brkL=W&(c>H60)&(prev(c)<=H60); brkS=W&(c<L60)&(prev(c)>=L60)
for lo_,hi_ in ((0,0.8),(0.8,1.5),(1.5,3),(3,99)):
    k=(RV>=lo_)&(RV<hi_); i=np.r_[np.where(brkL&k)[0],np.where(brkS&k)[0]]; d=np.r_[np.ones((brkL&k).sum()),-np.ones((brkS&k).sum())]
    r={'event':f'60-bar break, rel.vol {lo_}-{hi_} (follow)'}
    for kk in (0.03,0.06,0.12): p,n,N=pcont(i,d,kk); r[f'p{kk}']=round(p,3); r[f'z{kk}']=round(z(p,n),1)
    r['N']=N; rows.append(r)
# absorption: high rel volume, small range, at new 15-bar extreme -> fade
smallr=rg<0.7*a14
for thr in (2,3):
    L_=W&(l<=L15)&(RV>thr)&smallr; S_=W&(h>=H15)&(RV>thr)&smallr
    i=np.r_[np.where(L_)[0],np.where(S_)[0]]; d=np.r_[np.ones(L_.sum()),-np.ones(S_.sum())]
    r={'event':f'absorption at 15-bar extreme (RV>{thr}, small range) fade'}
    for kk in (0.03,0.06,0.12): p,n,N=pcont(i,d,kk); r[f'p{kk}']=round(p,3); r[f'z{kk}']=round(z(p,n),1)
    r['N']=N; rows.append(r)
# climax: very high RV and large range at extreme -> fade
L_=W&(l<=L15)&(RV>3)&(rg>2*a14)&(c<o); S_=W&(h>=H15)&(RV>3)&(rg>2*a14)&(c>o)
i=np.r_[np.where(L_)[0],np.where(S_)[0]]; d=np.r_[np.ones(L_.sum()),-np.ones(S_.sum())]
r={'event':'climax bar at 15-bar extreme (RV>3, range>2x) fade'}
for kk in (0.03,0.06,0.12): p,n,N=pcont(i,d,kk); r[f'p{kk}']=round(p,3); r[f'z{kk}']=round(z(p,n),1)
r['N']=N; rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))
# (b) overnight inventory correction: sign of (prev RTH close -> 09:30 open) vs first 30/60 min RTH return
print("\n== (b) overnight inventory: corr / hit-rate of fading overnight move in first RTH 30/60 min ==")
i0=np.where(m==571)[0]; i0=i0[~np.isnan(A[i0])&~np.isnan(pcl[i0])]
ovn=(o[i0]-pcl[i0])/A[i0]
for hz in (30,60):
    e=np.minimum(i0+hz-1,df.flat_rth.values[i0]); r1=(c[e]-o[i0])/A[i0]
    for y in (2023,2024,2025):
        k=YR[i0]==y; big=k&(np.abs(ovn)>0.3)
        print(f" {y} hz{hz}: corr(ovn, first{hz}m)={np.corrcoef(ovn[k],r1[k])[0,1]:+.3f}  fade-hit |ovn|>0.3: {(np.sign(r1[big])==-np.sign(ovn[big])).mean():.2f} (n={big.sum()})  mean fade ret {(-np.sign(ovn[big])*r1[big]).mean()*100:+.1f}%ATR")
