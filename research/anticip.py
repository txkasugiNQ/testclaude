from families import *
TH=0.16; r5=RET[5]
for w in ('am','all'):
    s=f6(th=TH,stp='sw5',w=w)
    T=run(df,s['sig'],s['dir'],s['stop'])
    si=T.si.values; d=T.dir.values
    # momentum ratio = directional ret5 / threshold
    ratio=lambda i,dd: dd*r5[i]/(TH*A[i])
    print(f"\n=== window={w}: N={len(T)} WR={T.win.mean()*100:.1f}")
    for k in (1,2,3,5,10,15,20):
        rr=ratio(si-k,d); print(f"  {k:2d} bars before signal: median momentum ratio={np.nanmedian(rr):.2f}  share >=0.5: {np.mean(rr>=0.5):.2f}  share >=0.75: {np.mean(rr>=0.75):.2f}")
    # lead time: consecutive bars with ratio>=0.5 before signal
    lead=[]
    for i,dd in zip(si,d):
        k=1
        while k<60 and ratio(i-k,dd)>=0.5: k+=1
        lead.append(k-1)
    T['lead']=lead
    T['lb']=pd.cut(T.lead,[-1,0,2,4,9,60],labels=['0','1-2','3-4','5-9','10+'])
    print("  lead time (bars ratio>=0.5 before signal) and WR:"); print(T.groupby('lb',observed=True).win.agg(['size','mean']).round(3).T.to_string())
    # pre-signal reliability: setup start = ratio crosses 0.5 (and 0.75) within window, aligned direction
    W=win(*WINS[w])
    for lvl in (0.5,0.75):
        for dd in (1,-1):
            rat=dd*r5/(TH*A); start=W&(rat>=lvl)&(prev(rat)<lvl)
            idx=np.where(start)[0]
            hit=np.array([np.any((dd*r5[i:i+11]>TH*A[i:i+11])) for i in idx])
            print(f"  setup start ratio>={lvl} dir={dd:+d}: N={len(idx)}  P(full signal within 10 bars)={hit.mean():.2f}")
