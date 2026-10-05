"""Descriptive structure studies B2 (flag/staircase) and B3 (first VWAP test after an opening drive).
For each event: entry reference, structural stop distance b, target distance a. Compare P(target first) with RW b/(a+b)."""
import sys
from families2 import *
import numba as nb
YR=df.ts.dt.year.values; flat=df.flat_rth.values
@nb.njit(cache=True)
def first_hit(h,l,idx,d,ent,a,b,flat):
    n=len(idx); res=np.zeros(n); mae=np.zeros(n); mfe=np.zeros(n)
    for k in range(n):
        t=idx[k]; tp=ent[k]+d[k]*a[k]; sl=ent[k]-d[k]*b[k]; mx=0.0; mn=0.0
        for j in range(t+1,flat[t]+1):
            fav=(h[j]-ent[k]) if d[k]>0 else (ent[k]-l[j]); adv=(ent[k]-l[j]) if d[k]>0 else (h[j]-ent[k])
            hs=(l[j]<=sl) if d[k]>0 else (h[j]>=sl); ht=(h[j]>=tp) if d[k]>0 else (l[j]<=tp)
            if hs and ht: res[k]=-1; mae[k]=b[k]; break
            if hs: res[k]=-1; mae[k]=b[k]; mfe[k]=max(mx,0); break
            if ht: res[k]=1; mae[k]=max(mn,0); mfe[k]=a[k]; break
            mx=max(mx,fav); mn=max(mn,adv)
        if res[k]==0:
            mae[k]=mn; mfe[k]=mx
    return res,mae,mfe
def report(name,idx,d,ent,a,b,years):
    sel=np.isin(YR[idx],years)&(b>0)&(a>0)
    idx,d,ent,a,b=idx[sel],d[sel],ent[sel],a[sel],b[sel]
    r,mae,mfe=first_hit(h,l,idx.astype(np.int64),d.astype(float),ent,a,b,flat)
    dec=r!=0; p=(r[dec]>0).mean(); rw=(b/(a+b))[dec].mean()
    ndays=len(np.unique(df.sd.values[idx]))
    print(f"{name:62s} N={len(idx):5d} ({len(idx)/max(ndays,1):.1f}/active day, {ndays} days) | P(target first)={p:.3f} vs RW {rw:.3f} -> edge {100*(p-rw):+.1f}pp | "
          f"median stop {np.median(b/A[idx]):.3f} ATR ({np.median(b):.0f} pts), RR {np.median(a/b):.2f} | MAE of winners P75 {np.quantile(mae[r>0]/b[r>0],.75):.2f}x stop")
years=(2023,) if len(sys.argv)<2 else tuple(int(x) for x in sys.argv[1].split(','))
W=win(575,930)
print("=== B2 FLAG / STAIRCASE: pole P bars, flag F bars, breakout close above flag high ===")
for P,F,X,q in ((15,10,0.15,0.4),(15,15,0.15,0.4),(20,15,0.2,0.4),(15,10,0.1,0.5),(30,20,0.2,0.4)):
    fh=hhv(h,F); fl=llv(l,F)
    ph_=prev(hhv(h,P),F); pl_=prev(llv(l,P),F); pc=prev(c,F)
    pole=ph_-pl_
    up=(pole>=X*A)&(pc>=pl_+0.7*pole)&((fh-fl)<=q*pole)&(fl>=ph_-0.5*pole)
    dn=(pole>=X*A)&(pc<=ph_-0.7*pole)&((fh-fl)<=q*pole)&(fh<=pl_+0.5*pole)
    # breakout bar: close beyond the flag of the PREVIOUS bar
    trL=W&(prev(up.astype(float))==1)&(c>prev(fh)); trS=W&(prev(dn.astype(float))==1)&(c<prev(fl))
    iL=np.where(trL)[0]; iS=np.where(trS)[0]
    i=np.r_[iL,iS]; d=np.r_[np.ones(len(iL)),-np.ones(len(iS))]
    ent=c[i]
    stop=np.where(d>0,prev(fl)[i]-TICK,prev(fh)[i]+TICK); b=np.abs(ent-stop)
    pl_i=prev(pole)[i]
    report(f"flag P{P} F{F} pole>={X}ATR q{q} target=1.0x pole",i,d,ent,pl_i,b,years)
    report(f"flag P{P} F{F} pole>={X}ATR q{q} target=0.5x pole",i,d,ent,0.5*pl_i,b,years)
    report(f"flag P{P} F{F} pole>={X}ATR q{q} target=1R (stop)",i,d,ent,b.copy(),b,years)
import sys as _s
if "--flagonly" in _s.argv: raise SystemExit
print("\n=== B3 FIRST VWAP TEST after an opening drive (no VWAP cross for >= N min, max distance >= X ATR) ===")
for N,X in ((15,0.1),(20,0.15),(30,0.15),(15,0.2)):
    rows_i=[];rows_d=[];ent=[];a=[];b=[];b2=[]
    for sd,g in df[rth&np.isin(YR,years)].groupby('sd'):
        idx=g.index.values
        if len(idx)<380 or np.isnan(A[idx[0]]): continue
        Aa=A[idx[0]]; side=0; maxd=0; start=None
        for t in idx[1:]:
            if m[t]>840: break
            v=vrw[t-1]   # VWAP known at prior bar close (causal touch level for bar t)
            if side==0:
                side=1 if c[t]>vrw[t] else -1; start=t; ext=h[t] if side>0 else l[t]; continue
            touched=(l[t]<=v) if side>0 else (h[t]>=v)
            if not touched:
                ext=max(ext,h[t]) if side>0 else min(ext,l[t]); maxd=max(maxd,abs(ext-vrw[t])); continue
            # first touch
            if (t-start)>=N and maxd>=X*Aa:
                rows_i.append(t); rows_d.append(side); ent.append(v); a.append(abs(ext-v)); b.append(0.33*abs(ext-v)); b2.append(0.05*Aa)
            break
    rows_i=np.array(rows_i); rows_d=np.array(rows_d,float); ent=np.array(ent); a=np.array(a); b=np.array(b); b2=np.array(b2)
    if len(rows_i)==0: continue
    # entry is a LIMIT at the VWAP touched on bar t: we evaluate from bar t+1 conservatively (fill bar excluded)
    report(f"VWAP 1st test N>={N}m dist>={X}: tgt=drive extreme, stop=1/3 drive beyond",rows_i,rows_d,ent,a,b,years)
    report(f"VWAP 1st test N>={N}m dist>={X}: tgt=drive extreme, stop=0.05 ATR beyond",rows_i,rows_d,ent,a,b2,years)
    report(f"VWAP 1st test N>={N}m dist>={X}: tgt=0.5x drive, stop=0.05 ATR beyond",rows_i,rows_d,ent,0.5*a,b2,years)
