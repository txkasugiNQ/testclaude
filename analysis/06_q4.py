import pandas as pd, numpy as np
pd.set_option('display.width',200)
df=pd.read_pickle('nq2.pkl'); D=pd.read_pickle('daily.pkl')
df['rng']=df.h-df.l
df=df.join(D[['atr14']],on='sd'); df['nr']=df.rng/df.atr14
# volatility by 30-min bucket (bar close time -> start = mod-1)
st=(df['mod']-1)%1440
df['b30']=(st//30)*30
prof=df.groupby('b30').agg(nr=('nr','mean'),v=('v','mean'))
prof['lbl']=[f"{int(b//60):02d}:{int(b%60):02d}" for b in prof.index]
prof['nr_rel']=prof.nr/prof.nr.mean()
print(prof.sort_values('nr',ascending=False).head(12)[['lbl','nr_rel','v']].round(2).to_string())
# top single minutes
pm=df.groupby(st).nr.mean(); pm=pm/pm.mean()
print("top minutes (start time) by rel range:", [(f"{i//60:02d}:{i%60:02d}",round(x,2)) for i,x in pm.nlargest(10).items()])
# HOD/LOD timing in RTH (full days)
fullsd=D.index[D.rn==390]
R=df[(df.ss=='RTH')&df.sd.isin(fullsd)]
ih=R.loc[R.groupby('sd').h.idxmax()]; il=R.loc[R.groupby('sd').l.idxmin()]
def hist(x):
    b=pd.cut(x['mod']-1,[570,585,600,630,660,720,780,840,900,930,945,960],right=False,
      labels=['09:30-45','09:45-10','10-10:30','10:30-11','11-12','12-13','13-14','14-15','15-15:30','15:30-45','15:45-16'])
    return b.value_counts(normalize=True).sort_index().round(3)
print("\nRTH HOD timing:\n",hist(ih).to_string()); print("\nRTH LOD timing:\n",hist(il).to_string())
both=pd.concat([hist(ih),hist(il)],axis=1)
# full ETH session H/L by sub-session
F=df[df.sd.isin(fullsd)]
eh=F.loc[F.groupby('sd').h.idxmax()].ss.value_counts(normalize=True); el=F.loc[F.groupby('sd').l.idxmin()].ss.value_counts(normalize=True)
print("\nETH day high in subsession:",eh.round(3).to_dict()); print("ETH day low in subsession:",el.round(3).to_dict())
# Opening range stats
out=[]
for n in [5,15,30,60]:
    orr=R[R['mod']<=570+n].groupby('sd').agg(oh=('h','max'),ol=('l','min'))
    x=orr.join(D[['rh','rl','atr14']])
    hod_in=(x.oh==x.rh).mean(); lod_in=(x.ol==x.rl).mean(); either=((x.oh==x.rh)|(x.ol==x.rl)).mean()
    bh=(x.rh>x.oh); bl=(x.rl<x.ol); bothb=(bh&bl).mean()
    w=(x.oh-x.ol)
    ext_up=((x.rh-x.oh)/w)[bh].median(); ext_dn=((x.ol-x.rl)/w)[bl].median()
    out.append([n,round(hod_in,3),round(lod_in,3),round(either,3),round(bothb,3),round((w/x.atr14).median(),3),round(ext_up,2),round(ext_dn,2)])
print("\nOR_min | P(OR high = RTH high) | P(OR low=RTH low) | P(either) | P(both sides broken) | ORwidth/ATR med | med ext up (OR multiples) | med ext dn")
for o in out: print(o)
