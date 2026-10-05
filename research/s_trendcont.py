"""Structure 'clean 2h trend closing at its extreme' (from motif clusters 2/9/27). 5-min decision points, causal.
Descriptive: P(target first) vs per-event RW, for structural stops."""
import sys
from structlib import *
years=tuple(int(x) for x in sys.argv[1].split(',')) if len(sys.argv)>1 else (2023,)
dec=rth&(m%5==0)&(m>=690)&(m<=900)&~np.isnan(A)          # decision at 5-min closes 11:30..15:00
N=120                                                     # 2h in 1-min bars
H2=hhv(h,N); L2=llv(l,N); net=c-prev(c,N-1)
rng=H2-L2; eff=np.abs(net)/rng
pos=(c-L2)/rng
H30=hhv(h,30); L30=llv(l,30)
for th_eff,rmin,pext in ((0.6,0.25,0.85),(0.7,0.25,0.85),(0.7,0.35,0.85),(0.8,0.25,0.9)):
    up=dec&(net>0)&(eff>=th_eff)&(rng>=rmin*A)&(pos>=pext)
    dn=dec&(net<0)&(eff>=th_eff)&(rng>=rmin*A)&(pos<=1-pext)
    # one event per day per side: first occurrence (avoid counting the same trend many times)
    up=once_per_day(up); dn=once_per_day(dn)
    i=np.r_[np.where(up)[0],np.where(dn)[0]]; d=np.r_[np.ones(up.sum()),-np.ones(dn.sum())]
    sel=np.isin(YR[i],years); i,d=i[sel],d[sel]
    ent=c[i]
    for stp in ('30m swing','0.5x 2h range'):
        st=np.where(d>0,L30[i]-TICK,H30[i]+TICK) if stp=='30m swing' else ent-d*0.5*rng[i]
        b=np.abs(ent-st)
        for tgtR in (1.0,2.0):
            a=tgtR*b
            r,mae,mfe=first_hit(h,l,i.astype(np.int64),d,ent,a,b,flat); dd=r!=0
            p=(r[dd]>0).mean(); rw=(b/(a+b))[dd].mean()
            print(f"{years} eff>={th_eff} rng>={rmin} ext>={pext} stop={stp:13s} tgt={tgtR}R: N={len(i)} ({len(i)/max(1,len(np.unique(df.sd.values[i]))):.1f}/day) P={p:.3f} RW={rw:.3f} edge {100*(p-rw):+.1f}pp | stop med {np.median(b/A[i]):.3f} ATR ({np.median(b):.0f}pts) | timeouts {(r==0).mean():.2f}")
