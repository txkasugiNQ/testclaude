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
