"""Stability-filtered pocket search: event x context, symmetric barriers. Select on 2023 halves only, test 2024 / 2025."""
import sys, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from obs_lab import *
EV=pd.read_pickle('obs_events.pkl')
mo=df.ts.dt.month.values
def p_on(idx,d,k,mask):
    idx=idx[mask]; d=d[mask]
    if len(idx)<30: return np.nan,0
    r=symbar(o,h,l,idx,d,k*A[idx],flat,120); dec=r!=0; n=dec.sum()
    return ((r[dec]>0).mean() if n else np.nan),n
vr_=df.atr60.values/df.atr390.values; ru_=(df.rh.values-df.rl.values)/A
CTX={'all':lambda i,d: np.ones(len(i),bool),
 'open 09:30-10:30':lambda i,d: m[i]<=630,'mid 10:30-14:00':lambda i,d:(m[i]>630)&(m[i]<=840),'late 14:00-15:30':lambda i,d: m[i]>840,
 'calm vol':lambda i,d: vr_[i]<1,'excited vol':lambda i,d: vr_[i]>=1,
 'with VWAP side':lambda i,d: np.sign(c[i]-vrw[i])==d,'against VWAP side':lambda i,d: np.sign(c[i]-vrw[i])==-d,
 'range used <0.6':lambda i,d: ru_[i]<0.6,'range used >=0.6':lambda i,d: ru_[i]>=0.6,
 'daily bull':lambda i,d: REG[i]==1,'daily bear':lambda i,d: REG[i]==0}
rows=[]
for en,(i,d) in EV.items():
    i=np.asarray(i,np.int64); d=np.asarray(d,float); ok=~np.isnan(A[i]); i,d=i[ok],d[ok]
    y=YR[i]; h1=(y==2023)&(mo[i]<=6); h2=(y==2023)&(mo[i]>6)
    for cn,cf in CTX.items():
        cm=cf(i,d)
        for k in (0.06,0.12):
            for sgn,lab in ((1,'follow'),(-1,'fade')):
                dd=d*sgn
                p1,n1=p_on(i,dd,k,cm&h1); p2,n2=p_on(i,dd,k,cm&h2)
                if n1<50 or n2<50: continue
                if p1>0.53 and p2>0.53:
                    p24,n24=p_on(i,dd,k,cm&(y==2024)); p25,n25=p_on(i,dd,k,cm&(y==2025))
                    rows.append(dict(event=en[:45],ctx=cn,s=k,dir=lab,p23H1=round(p1,3),p23H2=round(p2,3),n23=n1+n2,p2024=round(p24,3),p2025=round(p25,3),n2425=n24+n25))
R=pd.DataFrame(rows)
n_tested=sum(1 for _ in EV)*len(CTX)*2*2
print(f"tested combinations: {n_tested}; selected on 2023 halves: {len(R)}")
pd.set_option('display.width',250); print(R.sort_values('p2024',ascending=False).to_string(index=False))
if len(R):
    held=((R.p2024>0.5)&(R.p2025>0.5)).mean(); print(f"\nshare of selected pockets with p>0.5 in BOTH 2024 and 2025: {held:.2f}  (null expectation ~0.25)")
    print(f"mean p 2024: {R.p2024.mean():.3f}, mean p 2025: {R.p2025.mean():.3f}")
