"""Round 3 audit: stop sizes, MAE/MFE, losing-streak anatomy of previous candidates."""
from families3 import *
from families3 import _pack_rr
from mbl import mbl
import numba as nb
flat=df.flat_rth.values; a14=df.atr14.values
@nb.njit(cache=True)
def excursions(h,l,c,ei,xi,fill,d,flat):
    n=len(ei); out=np.zeros((n,4))
    for k in range(n):
        mae=0.0; mfe=0.0
        for j in range(ei[k],xi[k]+1):
            fav=(h[j]-fill[k])*d[k] if d[k]>0 else (fill[k]-l[j])
            adv=(fill[k]-l[j]) if d[k]>0 else (h[j]-fill[k])
            mfe=max(mfe,fav); mae=max(mae,adv)
        # unconstrained to EOD (ignoring stop)
        mae2=0.0; mfe2=0.0
        for j in range(ei[k],flat[ei[k]]+1):
            fav=(h[j]-fill[k]) if d[k]>0 else (fill[k]-l[j])
            adv=(fill[k]-l[j]) if d[k]>0 else (h[j]-fill[k])
            mfe2=max(mfe2,fav); mae2=max(mae2,adv)
        out[k,0]=mae; out[k,1]=mfe; out[k,2]=mae2; out[k,3]=mfe2
    return out
def audit(T,name):
    ei=T.ei.values.astype(np.int64); xi=T.xi.values.astype(np.int64); d=T.dir.values.astype(float)
    ex=excursions(h,l,c,ei,xi,T.fill.values,d,flat)
    R=T.R.values; Aa=A[T.si.values]
    print(f"\n######## {name}  N={len(T)}")
    print(f" SL distance: median {np.median(R):.1f} pts | mean {R.mean():.1f} | P10 {np.quantile(R,.1):.1f} | P90 {np.quantile(R,.9):.1f}")
    print(f" SL / daily ATR: median {np.median(R/Aa):.3f} | SL / atr14(1m): median {np.median(R/a14[T.si.values]):.1f}x one-minute ranges")
    for y in (2023,2024,2025):
        k=T.ts.dt.year.values==y; print(f"   {y}: median SL {np.median(R[k]):.1f} pts = {np.median(R[k]/Aa[k]):.3f} ATR (median ATR {np.median(Aa[k]):.0f})")
    w=T.win.values
    print(f" MAE (in R) winners: median {np.median(ex[w,0]/R[w]):.2f}, P75 {np.quantile(ex[w,0]/R[w],.75):.2f}, P90 {np.quantile(ex[w,0]/R[w],.9):.2f}")
    print(f" MFE (in R) losers : median {np.median(ex[~w,1]/R[~w]):.2f}, P75 {np.quantile(ex[~w,1]/R[~w],.75):.2f}  (how far losers went in favour first)")
    print(f" Unconstrained to EOD: MFE median {np.median(ex[:,3]/R):.2f}R, MAE median {np.median(ex[:,2]/R):.2f}R")
    # streak anatomy
    s=0; streaks=[]
    for v in w:
        if not v: s+=1
        else:
            if s: streaks.append(s)
            s=0
    if s: streaks.append(s)
    st=np.array(streaks); print(f" losing streaks: mean {st.mean():.2f}, max {st.max()}, P90 {np.quantile(st,.9):.0f}, share>=8: {(st>=8).mean()*100:.1f}%")
    # intraday clustering: P(win | previous trade same day lost/won)
    T2=T.assign(prev_win=T.groupby('sd').win.shift(1))
    a=T2[T2.prev_win==False].win.mean(); b=T2[T2.prev_win==True].win.mean(); c0=T2[T2.prev_win.isna()].win.mean()
    print(f" P(win | 1st trade of day)={c0:.3f}  P(win | prev same-day LOSS)={a:.3f}  P(win | prev same-day WIN)={b:.3f}")
    return ex
# candidates
from engine import run
s=f6(th=0.16,stp='sw5',w='am'); T1=run(df,s['sig'],s['dir'],s['stop']); T1['dir']=T1['dir'].astype(float)
audit(T1,'MBC (round 1, RR 0.6)')
T2=mbl(0.12,EOD,cancel=True); audit(T2,'MBL (round 2, stop entry, EOD)')
i=np.where((m==571)&~np.isnan(A))[0]; i=i[np.abs(c[i]-o[i])>0.03*A[i]]; d=np.sign(c[i]-o[i])
T3=_pack_rr(i,d,np.where(d>0,l[i]-TICK,h[i]+TICK),EOD,0); audit(T3,'OBR (round 2)')
