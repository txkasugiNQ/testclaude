from families3 import *
P=('2022-12-01','2024-01-01')
ropen=np.where(rth,pd.Series(np.where(m==571,o,np.nan)).groupby(df.sd.values).transform('max').values,np.nan)
r5=RET[5]
def base(th,w='all'):
    W=win(*WINS[w]); L_=W&(r5>th*A)&(prev(r5)<=th*A); S_=W&(r5<-th*A)&(prev(r5)>=-th*A)
    i=np.r_[np.where(L_)[0],np.where(S_)[0]]; d=np.r_[np.ones(L_.sum()),-np.ones(S_.sum())]; return i,d
def ev(i,d,lab):
    st=np.where(d>0,LLV[5][i]-TICK,HHV[5][i]+TICK)
    out=[]
    for rr,tb in ((2,0),(3,0),(EOD,0),(EOD,120)):
        R=(c[i]-st)*d; k=(R>=0.02*A[i])&(R<=0.6*A[i])
        T=run2(df,i[k],d[k],st[k],rr=rr,max_bars=tb); T=T[(T.sd>=P[0])&(T.sd<P[1])]
        s=stats2(T); out.append(f"{'EOD' if rr>1e5 else rr}{'/tb'+str(tb) if tb else ''}: PF {s['PF']:.2f} Exp {s['ExpR']:+.3f}")
    print(f"{lab:45s} N={s['N']:4d} | "+" | ".join(out))
for th in (0.12,0.16):
    i,d=base(th); print(f"\n## burst th={th}")
    ev(i,d,'all')
    day=np.sign(c[i]-ropen[i]); ev(i[day==d],d[day==d],'with day direction (vs RTH open)'); ev(i[day!=d],d[day!=d],'against day direction')
    vw=np.sign(c[i]-vrw[i]); ev(i[vw==d],d[vw==d],'on trend side of VWAP'); ev(i[vw!=d],d[vw!=d],'opposite side of VWAP')
    newx=np.where(d>0,h[i]>=df.rh.values[i],l[i]<=df.rl.values[i]); ev(i[newx],d[newx],'burst makes new RTH extreme'); ev(i[~newx],d[~newx],'burst inside RTH range')
    ru=(df.rh.values[i]-df.rl.values[i])/A[i]; ev(i[ru<0.5],d[ru<0.5],'day range used <0.5 ATR'); ev(i[ru>=0.5],d[ru>=0.5],'day range used >=0.5 ATR')
    vr=df.atr60.values[i]/df.atr390.values[i]; ev(i[vr<1],d[vr<1],'calm regime (atr60<atr390)'); ev(i[vr>=1],d[vr>=1],'excited regime')
    hr=(m[i]-1)//60; ev(i[hr<11],d[hr<11],'before 11:00'); ev(i[hr>=11],d[hr>=11],'after 11:00')
