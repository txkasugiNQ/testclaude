from mbl import *
from wf2 import wf, score, DAYS, stats2
import json
WINDOWS={'09:35-10:30':(575,630),'09:35-11:30':(575,690),'09:35-13:00':(575,780),'09:35-15:30':(575,930),'10:30-15:30':(630,930),'excl 11:30-13:30':None}
trades={}
for wn,wv in WINDOWS.items():
    for sf in (0.75,1.0):
        if wv is None:
            i,pL,sL,pS,sS,ex=mbl_orders(0.12,(575,930)); keep=~((m[i]>690)&(m[i]<=810)); i,pL,sL,pS,sS,ex=i[keep],pL[keep],sL[keep],pS[keep],sS[keep],ex[keep]
        else: i,pL,sL,pS,sS,ex=mbl_orders(0.12,wv)
        trades[json.dumps({'win':wn,'stop':sf})]=run_oco2(df,i,pL,sL,pS,sS,ex,stop_frac=sf)
nd=df[df.sd>='2024-01-01'].sd.nunique()
print("fixed view per window (stop 1.0):")
for k,T in trades.items():
    p=json.loads(k)
    if p['stop']!=1.0: continue
    out=[]
    for y in (2023,2024,2025):
        x=T[T.ts.dt.year==y]; out.append(f"{y} PF {x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum():.2f} N{len(x)}")
    ss=streak_stats(T); print(f"  {p['win']:18s} "+" | ".join(out)+f" | maxLS {ss['maxLS']} avgLS {ss['avgLS']}")
for fmin in (0.5,1.0,1.5):
    O,sel=wf(trades,fmin); s=stats2(O,nd); a=stats2(O); ss=streak_stats(O)
    print(f"WF time-window selection fmin={fmin}: N={s['N']} WR={s['WR']} PF={s['PF']} Exp={s['ExpR']:+.3f} maxLS={ss['maxLS']} avgLS={ss['avgLS']} TPD={a['TPD']} | picks: "+", ".join(json.loads(x[1])['win']+'/'+str(json.loads(x[1])['stop']) for x in sel))
# losing streak anatomy on full-window MBL
T=trades[json.dumps({'win':'09:35-15:30','stop':1.0})].copy()
T['hour']=(m[T.ei.values]-1)//60; T['vol']=pd.qcut(pd.Series(A[T.si.values]).rank(pct=True),3,labels=['low','mid','high']).values
T['regime']=np.where(REG[T.si.values]==1,'bull','bear')
# assign each trade to the streak it belongs to (losing streak id)
w=T.win.values; sid=np.zeros(len(w),int); cur=0; ln=np.zeros(len(w),int)
run_=0
for j,v in enumerate(w):
    if not v: run_+=1
    else: run_=0
    ln[j]=run_
T['in_long_streak']=False
# mark trades that are part of a losing streak >=6
j=0
while j<len(w):
    if not w[j]:
        k=j
        while k<len(w) and not w[k]: k+=1
        if k-j>=6: T.iloc[j:k,T.columns.get_loc('in_long_streak')]=True
        j=k
    else: j+=1
print("\nshare of trades inside losing streaks >=6, by hour / vol / regime (vs share of all trades):")
for col in ('hour','vol','regime'):
    g=T.groupby(col,observed=True).agg(n=('win','size'),longstreak=('in_long_streak','mean'),wr=('win','mean')).round(3); print(g.to_string())
mon=T.groupby(T.ts.dt.to_period('M')).in_long_streak.mean(); print("months with most long-streak trades:",mon.sort_values(ascending=False).head(6).round(2).to_dict())
