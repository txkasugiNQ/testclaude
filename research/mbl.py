"""MBL - Momentum Burst Level: final candidate definitions"""
from families3 import *
def mbl_orders(th=0.12,w=(575,930),N=5,valid=5):
    W=rth&(m>w[0])&(m<=w[1])&~np.isnan(A); r5=c-prev(c,N)
    L_=W&(r5>th*A)&(prev(r5)<=th*A); S_=W&(r5<-th*A)&(prev(r5)>=-th*A)
    i=np.r_[np.where(L_)[0],np.where(S_)[0]]; d=np.r_[np.ones(L_.sum()),-np.ones(S_.sum())]
    o_=np.argsort(i); i,d=i[o_],d[o_]
    hi=HHV[5][i] if N==5 else hhv(h,N)[i]; lo=LLV[5][i] if N==5 else llv(l,N)[i]
    k=((hi-lo)>=0.02*A[i])&((hi-lo)<=0.6*A[i]); i,d,hi,lo=i[k],d[k],hi[k],lo[k]
    pxL=np.where(d>0,hi+TICK,np.nan); slL=np.where(d>0,lo-TICK,np.nan)
    pxS=np.where(d<0,lo-TICK,np.nan); slS=np.where(d<0,hi+TICK,np.nan)
    return i,pxL,slL,pxS,slS,np.minimum(i+valid,df.flat_rth.values[i])
def mbl(th=0.12,rr=EOD,tb=0,cancel=False,w=(575,930),slip=1):
    i,pL,sL,pS,sS,ex=mbl_orders(th,w)
    return run_oco(df,i,pL,sL,pS,sS,expiry=ex,rr=rr,max_bars=tb,cancel_inv=cancel,slip_ticks=slip)
if __name__=='__main__':
    for th in (0.12,0.16):
        for rr,lab in ((3,'rr3'),(EOD,'EOD')):
            for cancel in (False,True):
                T=mbl(th,rr,cancel=cancel)
                ys=[]
                for y in (2023,2024,2025):
                    x=T[T.ts.dt.year==y]; ys.append(f"{y}: PF {x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum():.2f} N {len(x)}")
                print(f"th={th} {lab} cancel={cancel}: "+" | ".join(ys))
