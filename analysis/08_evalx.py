import pandas as pd, numpy as np, sys
df=pd.read_pickle('nq2.pkl'); D=pd.read_pickle('daily.pkl'); L=pd.read_pickle('levels.pkl')
fullsd=D.index[(D.rn==390)&D.atr14.notna()]
R=df[(df.ss=='RTH')&df.sd.isin(fullsd)]
S={sd:(g.o.values[0],g.h.values,g.l.values) for sd,g in R.groupby('sd')}
def ev(o,h,l,lvl,Rpts):
    """returns 1 reversal, 0 break, nan untouched/undecided. side by RTH open."""
    if lvl>o:   # resistance
        t=np.argmax(h>=lvl)
        if h[t]<lvl: return np.nan,False
        if h[t]>=lvl+Rpts: return 0,True
        hb=h[t+1:]>=lvl+Rpts; lr=l[t+1:]<=lvl-Rpts
    else:
        t=np.argmax(l<=lvl)
        if l[t]>lvl: return np.nan,False
        if l[t]<=lvl-Rpts: return 0,True
        hb=l[t+1:]<=lvl-Rpts; lr=h[t+1:]>=lvl+Rpts
    ib=np.argmax(hb) if hb.any() else 10**6; ir=np.argmax(lr) if lr.any() else 10**6
    if ib==ir==10**6: return np.nan,True
    if ib==ir: return 0,True   # same bar: conservative = break
    return float(ir<ib),True
offs=[-0.3,-0.2,-0.1,0.1,0.2,0.3]
def run(col,Rk=0.10,years=None):
    real=[];ctrl=[];touch=0;n=0
    for sd in fullsd:
        if years and sd.year not in years: continue
        lv=L.at[sd,col]
        if np.isnan(lv): continue
        o,h,l=S[sd]; A=D.at[sd,'atr14']; Rp=Rk*A; n+=1
        r,tch=ev(o,h,l,lv,Rp); touch+=tch
        if not np.isnan(r): real.append(r)
        for k in offs:
            c,_=ev(o,h,l,lv+k*A,Rp)
            if not np.isnan(c): ctrl.append(c)
    real=np.array(real); ctrl=np.array(ctrl)
    p=real.mean(); pc=ctrl.mean(); se=np.sqrt(p*(1-p)/len(real))
    return dict(level=col,days=n,touch_rate=round(touch/n,3),N=len(real),hold=round(p,3),ctrl=round(pc,3),edge=round(p-pc,3),z=round((p-pc)/se,2))
cols=[c for c in L.columns]
Rk=float(sys.argv[1]) if len(sys.argv)>1 else 0.10
res=[]
for c in cols:
    a=run(c,Rk); b=run(c,Rk,{2023,2024}); c2=run(c,Rk,{2025})
    a['IS_edge']=b['edge']; a['OOS_edge']=c2['edge']; a['OOS_z']=c2['z']; res.append(a)
out=pd.DataFrame(res).sort_values('edge',ascending=False)
print(f"R = {Rk} x ATR14"); print(out.to_string(index=False))
