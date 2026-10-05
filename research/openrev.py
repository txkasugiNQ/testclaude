"""ORV - Opening Reversal through the open: level-based strategy simulator (bar-by-bar, causal)."""
from families2 import *
import numba as nb
flat=df.flat_rth.values
@nb.njit(cache=True)
def sim_orv(o,h,l,c,A,m,day_start,flat,X,t_arm_end,t_entry_end,entry_mode,stop_frac,k_tgt,tick,slip,comm):
    """day_start: index of first RTH bar (09:30-09:31) per day.
    Arm when |running extreme - open| >= X*A within bars with close-time <= t_arm_end.
    entry_mode 0: SELL/BUY-STOP at open -/+ 1 tick (fill on touch, at min/max(level, bar open) -/+ slip)
    entry_mode 1: close beyond the open -> market at next bar open (+slip)
    Entry allowed only on bars with close-time <= t_entry_end. Stop = open + d_early*stop_frac*exc (+tick) [stop_frac=1 -> early extreme];
    target = open - d_early*k_tgt*exc. Flat at session flat. On the entry bar only the stop is checked."""
    nd=len(day_start); out=np.full((nd,10),np.nan); k=0
    for di in range(nd):
        s0=day_start[di]; fe=flat[s0]; O=o[s0]; Aa=A[s0]
        if np.isnan(Aa): continue
        hi=-1e18; lo=1e18; armed=0; t=s0; entered=False
        while t<=fe and m[t]<=t_entry_end:
            # arming uses bars up to t (inclusive) - but the entry level only becomes active from the NEXT bar
            if armed!=0 and not entered:
                d=-armed
                if entry_mode==0:
                    lvl=O-tick if d<0 else O+tick
                    trig=(l[t]<=lvl) if d<0 else (h[t]>=lvl)
                    if trig:
                        fill=(min(lvl,o[t]) if d<0 else max(lvl,o[t]))-(-d)*0.0
                        fill=fill+d*slip
                        entered=True; eb=t
                else:
                    if (d<0 and c[t-1]<O) or (d>0 and c[t-1]>O):
                        fill=o[t]+d*slip; entered=True; eb=t
                if entered:
                    E=hi if armed==1 else lo; exc=abs(E-O)
                    stop=O+armed*stop_frac*exc+armed*tick
                    tgt=O-armed*k_tgt*exc
                    R=(stop-fill)*armed
                    if R<=tick or (tgt-fill)*d<=0:
                        entered=False; break
                    break
            hi=max(hi,h[t]); lo=min(lo,l[t])
            if armed==0 and m[t]<=t_arm_end:
                if hi-O>=X*Aa: armed=1
                elif O-lo>=X*Aa: armed=-1
            t+=1
        if not entered: continue
        # manage
        e=eb; code=-1; ex=np.nan; mae=0.0; mfe=0.0
        while e<=fe:
            slh=(h[e]>=stop) if d<0 else (l[e]<=stop)
            tph=((l[e]<=tgt-tick) if d<0 else (h[e]>=tgt+tick)) and e!=eb
            if slh:
                gap=(o[e]>stop) if d<0 else (o[e]<stop)
                ex=(o[e] if (gap and e!=eb) else stop)-d*slip; code=0; mae=R; break
            adv=(h[e]-fill) if d<0 else (fill-l[e]); fav=(fill-l[e]) if d<0 else (h[e]-fill)
            mae=max(mae,adv); mfe=max(mfe,fav)
            if tph:
                ex=tgt; code=1; break
            e+=1
        if code==-1:
            e=fe; ex=c[e]-d*slip; code=2
        out[k,0]=eb; out[k,1]=e; out[k,2]=fill; out[k,3]=R; out[k,4]=(ex-fill)*d-comm; out[k,5]=code; out[k,6]=d; out[k,7]=exc; out[k,8]=mae/R; out[k,9]=mfe/R
        k+=1
    return out[:k]
DAY0=np.where(m==571)[0]
def orv(X=0.15,t_arm_end=630,t_entry_end=660,entry='stop',stop_frac=1.0,k=0.5,slip_ticks=1):
    r=sim_orv(o,h,l,c,A,m,DAY0.astype(np.int64),flat,X,t_arm_end,t_entry_end,0 if entry=='stop' else 1,stop_frac,k,TICK,slip_ticks*TICK,COMM)
    T=pd.DataFrame(r,columns=['ei','xi','fill','R','pnl','code','dir','exc','maeR','mfeR'])
    for kk in ['ei','xi','code']: T[kk]=T[kk].astype(int)
    T['si']=T.ei-1; T['ts']=df.ts.values[T.ei.values]; T['sd']=df.sd.values[T.ei.values]; T['win']=T.pnl>0; T['pnlR']=T.pnl/T.R
    return T
if __name__=='__main__':
    rows=[]
    for X in (0.1,0.15):
     for te in (630,660):
      for entry in ('stop','close'):
       for sf in (1.0,0.75,0.5):
        for k in (0.5,0.75,1.0):
          T=orv(X,te,te,entry,sf,k)
          for y in (2023,2024,2025):
            x=T[T.ts.dt.year==y]; s=stats(x); ss=streak_stats(x)
            rows.append(dict(X=X,end=te,entry=entry,stop=sf,k=k,yr=y,N=s['N'],WR=s['WR'],PF=s['PF'],Exp=s['ExpR'],maxLS=ss['maxLS'],medR=s['medR']))
    R=pd.DataFrame(rows)
    P=R.pivot_table(index=['X','end','entry','stop','k'],columns='yr',values=['WR','PF','Exp','maxLS','N','medR'])
    P.columns=[f'{a}{str(b)[2:]}' for a,b in P.columns]
    pd.set_option('display.width',260); print(P.round(2).sort_values('Exp23',ascending=False).to_string())
