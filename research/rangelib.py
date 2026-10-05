"""Range -> Deviation research library. All ranges are frozen at formation end; deviations only used afterwards (causal)."""
from families2 import *
import numba as nb
YR=df.ts.dt.year.values; flat=df.flat_rth.values; IDX=np.arange(len(df))
key=df.sd.values
def session_ranges(form_mask, valid_lo, valid_hi):
    """one range per session day: formed over form_mask bars, valid on bars with close-time in (valid_lo, valid_hi] after formation."""
    g=pd.DataFrame({'sd':key,'i':IDX,'h':h,'l':l,'f':form_mask,'v':(m>valid_lo)&(m<=valid_hi)})
    F=g[g.f].groupby('sd').agg(H=('h','max'),L=('l','min'),fe=('i','max'))
    V=g[g.v].groupby('sd').agg(vs=('i','min'),ve=('i','max'))
    R=F.join(V,how='inner'); R=R[R.vs>R.fe]
    return R[['H','L','fe','vs','ve']].values
def prior_day_ranges():
    g=pd.DataFrame({'sd':key,'i':IDX,'h':h,'l':l})
    F=g[rth].groupby('sd').agg(H=('h','max'),L=('l','min'),fe=('i','max'))
    V=g[rth&(m>575)&(m<=930)].groupby('sd').agg(vs=('i','min'),ve=('i','max'))
    F=F.shift(1); R=F.join(V,how='inner').dropna(); R=R[R.vs>R.fe]
    return R[['H','L','fe','vs','ve']].values
def hour_ranges():
    out=[]
    for a in range(570,900,60):          # blocks 09:30-10:30 ... 14:30-15:30 ; valid next 60 min (entries <=15:30)
        fm=rth&(m>a)&(m<=a+60)
        R=session_ranges(fm,a+60,min(a+120,930)); out.append(R)
    return np.vstack(out)
@nb.njit(cache=True)
def _boxes(h,l,A,rthwin,N,q,valid_n):
    out=[]; n=len(h); t=N; busy_until=-1
    while t<n:
        if rthwin[t] and t>busy_until and not np.isnan(A[t]):
            H=h[t-N+1:t+1].max(); L=l[t-N+1:t+1].min()
            if H-L<q*A[t] and H-L>0:
                out.append((H,L,t,t+1,min(t+valid_n,n-1)))
                busy_until=t+valid_n
        t+=1
    return out
def box_ranges(N,q,valid_n=60):
    win_=rth&(m>575)&(m<=900)
    b=_boxes(h,l,A,win_,N,q,valid_n)
    R=np.array(b,dtype=float)
    # validity must stay within the same session RTH window
    keep=[]
    for H_,L_,fe,vs,ve in R:
        fe,vs,ve=int(fe),int(vs),int(ve)
        ve2=min(ve,flat[fe]-29)        # no entries in last 30 min
        if ve2>vs and key[vs]==key[fe]: keep.append((H_,L_,fe,vs,ve2))
    return np.array(keep)
RANGES={}
def build_all():
    RANGES['OR15']=session_ranges(rth&(m>570)&(m<=585),585,930)
    RANGES['OR30']=session_ranges(rth&(m>570)&(m<=600),600,930)
    RANGES['IB60']=session_ranges(rth&(m>570)&(m<=630),630,930)
    RANGES['PREMKT 08-09:30']=session_ranges((m>480)&(m<=570),570,930)
    RANGES['OVERNIGHT 18-09:30']=session_ranges((m>1080)|(m<=570),570,930)
    RANGES['ASIA 18-02 (valid London+NY)']=session_ranges((m>1080)|(m<=120),120,930)
    RANGES['LONDON 02-08:30']=session_ranges((m>120)&(m<=510),510,930)
    RANGES['PRIOR DAY RTH']=prior_day_ranges()
    RANGES['HOURLY BLOCK (next hour)']=hour_ranges()
    RANGES['BOX 30 bars <0.10 ATR']=box_ranges(30,0.10)
    RANGES['BOX 60 bars <0.15 ATR']=box_ranges(60,0.15)
    return RANGES
@nb.njit(cache=True)
def first_touches(h,l,R,k,unit_mode,A):
    """for each range and side, first bar in validity where the deviation level is touched.
    unit_mode 0: deviation = k * range width ; 1: deviation = k * daily ATR. returns rows (t, level, dir_out, W)"""
    out=[]
    for r in range(R.shape[0]):
        H=R[r,0]; L=R[r,1]; vs=int(R[r,3]); ve=int(R[r,4]); W=H-L
        if W<=0: continue
        dev=k*W if unit_mode==0 else k*A[vs]
        if np.isnan(dev): continue
        up=H+dev; dn=L-dev; tu=-1; td=-1
        for t in range(vs,ve+1):
            if tu<0 and h[t]>=up: tu=t
            if td<0 and l[t]<=dn: td=t
            if tu>=0 and td>=0: break
        if tu>=0: out.append((tu,up,1.0,W))
        if td>=0: out.append((td,dn,-1.0,W))
    return out
@nb.njit(cache=True)
def touch_outcomes(o,h,l,c,ev_t,lvl,d,s_up,s_dn,flat,tick):
    """At the touch bar t of level lvl (price arriving in direction d):
    CONT = stop entry at lvl (fill max(lvl,open) in direction d); REV = limit entry at lvl in direction -d (needs trade-through 1 tick).
    Both evaluated with target s_up (in trade direction) / stop s_dn from the fill price; on the fill bar only the stop is checked.
    returns cont_res, rev_res (+1/-1/0), cont_mfe, cont_mae (to flat, from lvl, in price)"""
    n=len(ev_t); cr=np.zeros(n); rr=np.zeros(n); mfe=np.zeros(n); mae=np.zeros(n)
    for k in range(n):
        t=int(ev_t[k]); fe=flat[t]; D=lvl[k]; dd=d[k]
        # continuation stop-entry
        fill=max(D,o[t]) if dd>0 else min(D,o[t])
        tp=fill+dd*s_up[k]; sl=fill-dd*s_dn[k]; res=0.0
        for j in range(t,fe+1):
            hs=(l[j]<=sl) if dd>0 else (h[j]>=sl)
            ht=((h[j]>=tp) if dd>0 else (l[j]<=tp)) and j>t
            if hs: res=-1.0; break
            if ht: res=1.0; break
        cr[k]=res
        # reversion limit entry at D (direction -dd)
        filled=(h[t]>=D+tick) if dd>0 else (l[t]<=D-tick)
        if filled:
            e=-dd; tp=D+e*s_up[k]; sl=D-e*s_dn[k]; res=0.0
            for j in range(t,fe+1):
                hs=(l[j]<=sl) if e>0 else (h[j]>=sl)
                ht=((h[j]>=tp) if e>0 else (l[j]<=tp)) and j>t
                if hs: res=-1.0; break
                if ht: res=1.0; break
            rr[k]=res
        else:
            rr[k]=np.nan
        mx=0.0; mn=0.0
        for j in range(t+1,fe+1):
            fav=(h[j]-D)*dd if dd>0 else (D-l[j]); adv=(D-l[j]) if dd>0 else (h[j]-D)
            mx=max(mx,fav); mn=max(mn,adv)
        mfe[k]=mx; mae[k]=mn
    return cr,rr,mfe,mae
def events(name,k,unit='W'):
    R=RANGES[name]
    ev=first_touches(h,l,R.astype(np.float64),float(k),0 if unit=='W' else 1,A)
    if len(ev)==0: return None
    E=np.array(ev); return E[:,0].astype(np.int64),E[:,1],E[:,2],E[:,3]

@nb.njit(cache=True)
def close_events(h,l,c,R,k,mode,nrec):
    """mode 0 (C): first CLOSE beyond deviation -> continuation (dir = out of range).
       mode 1 (E/F sweep&reclaim): first touch of deviation, then within nrec bars a CLOSE back on the inside of the deviation -> reversal.
       returns (t_decision, dir_trade, W, level)"""
    out=[]
    for r in range(R.shape[0]):
        H=R[r,0]; L=R[r,1]; vs=int(R[r,3]); ve=int(R[r,4]); W=H-L
        if W<=0: continue
        up=H+k*W; dn=L-k*W
        for side in (1,-1):
            lv=up if side>0 else dn
            if mode==0:
                for t in range(vs,ve+1):
                    if (side>0 and c[t]>lv) or (side<0 and c[t]<lv):
                        out.append((t,float(side),W,lv)); break
            else:
                tt=-1
                for t in range(vs,ve+1):
                    if (side>0 and h[t]>=lv) or (side<0 and l[t]<=lv):
                        tt=t; break
                if tt<0: continue
                for t in range(tt,min(tt+nrec,ve)+1):
                    if (side>0 and c[t]<lv) or (side<0 and c[t]>lv):
                        out.append((t,float(-side),W,lv)); break
    return out
@nb.njit(cache=True)
def sym_from_close(o,h,l,c,ts,d,s,flat):
    """symmetric barriers +-s around the decision close c[t]; evaluated from t+1 (decision price = close, conservative tie = 0)"""
    n=len(ts); res=np.zeros(n)
    for k in range(n):
        t=ts[k]; e=c[t]; up=e+s[k]; dn=e-s[k]
        for j in range(t+1,flat[t]+1):
            hu=h[j]>=up; hd=l[j]<=dn
            if hu and hd: break
            if hu: res[k]=d[k]; break
            if hd: res[k]=-d[k]; break
    return res
