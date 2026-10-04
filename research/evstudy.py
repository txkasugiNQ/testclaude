"""Event study: signed forward returns (ATR units) from next-bar open. Discovery on 2023 only."""
from families2 import *
flat=df.flat_rth.values; sdv=df.sd.values
YR=df.ts.dt.year.values
def fwd(idx,d,hz):
    j=idx+1; ok=j<len(o)
    ent=o[np.minimum(j,len(o)-1)]
    if hz=='eod': ex=c[flat[idx]]
    else:
        e=np.minimum(idx+hz,flat[idx]); ex=c[e]
    return d*(ex-ent)/A[idx]
def study(name,idx,d,years=(2023,),hz=(15,30,60,120,'eod'),verbose=True):
    idx=np.asarray(idx); d=np.asarray(d,float)
    sel=np.isin(YR[idx],years)&~np.isnan(A[idx]); idx,d=idx[sel],d[sel]
    if len(idx)<20: return None
    res={'event':name,'N':len(idx),'perday':round(len(idx)/max(1,len(np.unique(sdv[idx]))),2)}
    for hh in hz:
        r=fwd(idx,d,hh); r=r[~np.isnan(r)]
        res[f'm{hh}']=round(r.mean()*100,2); res[f't{hh}']=round(r.mean()/r.std()*np.sqrt(len(r)),1)
    return res
