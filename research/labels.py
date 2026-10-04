from feats import *
@nb.njit(cache=True)
def lab(o,h,l,c,cand,Rp,flat,rr,tick,comm):
    n=len(cand); out=np.full((n,2),np.nan); bars=np.full((n,2),-1)
    for s in range(n):
        t=cand[s]; j=t+1; R=Rp[s]
        if j>flat[t] or np.isnan(R): continue
        for di in range(2):
            d=1.0 if di==0 else -1.0
            fill=o[j]+d*tick; st=fill-d*R; tp=fill+d*rr*R
            res=np.nan; e=j
            while e<=flat[t]:
                if d>0: slh=l[e]<=st; tph=h[e]>=tp+tick
                else:   slh=h[e]>=st; tph=l[e]<=tp-tick
                if slh: res=0.0; break
                if tph: res=1.0; break
                e+=1
            if np.isnan(res):
                e=flat[t]; res=1.0 if ((c[e]-d*tick-fill)*d-comm)>0 else 0.0
            out[s,di]=res; bars[s,di]=e-j
    return out,bars
if __name__=='__main__':
    df=build(); m=df['mod'].values
    cand=np.where(df.rth.values&(m>=575)&(m<=930)&~np.isnan(df.atrD.values))[0]
    L=pd.DataFrame({'i':cand})
    for k in (0.05,0.1,0.15,0.2):
        out,bars=lab(df.o.values,df.h.values,df.l.values,df.c.values,cand,k*df.atrD.values[cand],df.flat_rth.values,RR,TICK,COMM)
        L[f'L{k}']=out[:,0]; L[f'S{k}']=out[:,1]; L[f'bL{k}']=bars[:,0]; L[f'bS{k}']=bars[:,1]
        print(k, np.nanmean(out[:,0]).round(4), np.nanmean(out[:,1]).round(4))
    L.to_pickle('labels.pkl')
