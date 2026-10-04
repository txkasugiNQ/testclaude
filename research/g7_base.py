from families3 import *
from families3 import _pack_rr
i=np.where((m==571)&~np.isnan(A))[0]; mv=c[i]-o[i]
def go(d,lab,k=0.03):
    sel=np.abs(mv)>k*A[i]; ii=i[sel]; dd=d[sel]
    st=np.where(dd>0,l[ii]-TICK,h[ii]+TICK)
    # for the stop to make sense the entry must be on the right side: long stop below bar low is fine either way
    T=_pack_rr(ii,dd,st,EOD,0)
    for per,(a,b) in (('2023',('2022-12-01','2024-01-01')),('2024-25',('2024-01-01','2026-01-01'))):
        x=T[(T.sd>=a)&(T.sd<b)]; s=stats2(x); print(f"{lab:22s} {per}: N={s['N']} WR={s['WR']} PF={s['PF']} Exp={s['ExpR']:+.3f} medR={s['medR']}")
go(np.sign(mv),'follow opening bar')
go(-np.sign(mv),'fade opening bar')
rng=np.random.default_rng(0)
for s in range(3): go(rng.choice([-1.0,1.0],len(i)),f'random dir #{s}')
go(np.ones(len(i)),'always long')
go(-np.ones(len(i)),'always short')
