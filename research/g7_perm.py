from families3 import *
import engine
i=np.where((m==571)&~np.isnan(A))[0]; mv=c[i]-o[i]
sel=np.abs(mv)>0.03*A[i]; i=i[sel]; mv=mv[sel]
rng_=h[i]-l[i]+2*TICK
def pf_for(d,period):
    st=c[i]-d*rng_            # symmetric stop distance = opening bar range (approx, measured from close)
    T=run2(df,i,d,st,rr=EOD)
    T=T[(T.sd>=period[0])&(T.sd<period[1])]
    r=T.pnlR; return r[r>0].sum()/-r[r<0].sum(), r.mean()
for per in (('2022-12-01','2024-01-01'),('2024-01-01','2026-01-01')):
    pf0,e0=pf_for(np.sign(mv),per)
    rs=np.random.default_rng(1); dist=np.array([pf_for(rs.choice([-1.0,1.0],len(i)),per) for _ in range(300)])
    print(per,f"follow PF {pf0:.2f} Exp {e0:+.3f} | random PF median {np.median(dist[:,0]):.2f}, 90% band [{np.quantile(dist[:,0],0.05):.2f},{np.quantile(dist[:,0],0.95):.2f}] | percentile of follow: {(dist[:,0]<pf0).mean()*100:.0f}%")
