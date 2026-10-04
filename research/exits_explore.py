"""Exploration (2023 only): expectancy vs RR / exit style for several entry events."""
from families2 import *
import engine
EOD=1e6
def evaluate(name,sig,dirn,stop,period=('2022-12-01','2024-01-01')):
    out=[]
    for rr in (0.5,1,1.5,2,3,EOD):
        T=run(df,sig,dirn,stop,rr=rr)
        T=T[(T.sd>=period[0])&(T.sd<period[1])]
        st=stats(T); out.append(f"rr={'EOD' if rr==EOD else rr}: WR {st['WR']:.0f} PF {st['PF']:.2f} Exp {st['ExpR']:+.3f}")
    print(f"{name:28s} N={st['N']:4d} | "+" | ".join(out))
W=win(575,930)
# A momentum bursts
for th in (0.08,0.16):
    s=f6(th=th,stp='sw5',w='all'); evaluate(f"burst th{th} sw5",s['sig'],s['dir'],s['stop'])
# B level breakouts (close beyond, market next open), stop = level -/+ 0.05A  or swing5
for lv_up,lv_dn in zip(UPPER,LOWER):
    for stp in ('lvl','sw5'):
        iL=np.where(first_cross(LEV[lv_up],1,W))[0]; iS=np.where(first_cross(LEV[lv_dn],-1,W))[0]
        sig=np.r_[iL,iS]; d=np.r_[np.ones(len(iL)),-np.ones(len(iS))]
        if stp=='lvl': st=np.r_[LEV[lv_up][iL]-0.05*A[iL],LEV[lv_dn][iS]+0.05*A[iS]]
        else: st=np.r_[LLV[5][iL]-TICK,HHV[5][iS]+TICK]
        R=(c[sig]-st)*d; k=(R>=0.02*A[sig])&(R<=0.5*A[sig])
        evaluate(f"BO {lv_up}/{lv_dn} stop={stp}",sig[k],d[k],st[k])
