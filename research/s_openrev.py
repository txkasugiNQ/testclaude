"""Structure study B1 'Opening reversal through the RTH open' (descriptive, 2023 unless --all)."""
import sys
from families2 import *
YR=df.ts.dt.year.values; flat=df.flat_rth.values
years=(2023,) if len(sys.argv)<2 else tuple(int(x) for x in sys.argv[1].split(','))
def study(X,TEND):
    rows=[]
    for sd,g in df[rth&np.isin(YR,years)].groupby('sd'):
        idx=g.index.values
        if len(idx)<380 or np.isnan(A[idx[0]]): continue
        ro=o[idx[0]]; Aa=A[idx[0]]
        hi=-1e9; lo=1e9; armed=0; ext=np.nan; t_arm=-1
        for t in idx:
            if m[t]>TEND: break
            hi=max(hi,h[t]); lo=min(lo,l[t])
            if armed==0:
                if hi-ro>=X*Aa: armed=1     # early move UP happened
                elif ro-lo>=X*Aa: armed=-1
            if armed!=0:
                # re-cross: close back on the other side of the open
                if (armed==1 and c[t]<ro) or (armed==-1 and c[t]>ro):
                    d=-armed; E=hi if armed==1 else lo; exc=abs(E-ro)
                    # forward path from next bar to session flat
                    fw=np.arange(t+1,flat[t]+1)
                    fav=(ro-l[fw]) if d<0 else (h[fw]-ro)          # favourable move measured from the OPEN
                    adv_ext=(h[fw]>=E) if d<0 else (l[fw]<=E)      # early extreme retaken?
                    first_ext=np.argmax(adv_ext) if adv_ext.any() else 10**6
                    def reach(k):
                        hit=fav>=k*exc; f=np.argmax(hit) if hit.any() else 10**6
                        return f<first_ext
                    # adverse excursion back across the open (in units of exc) before reaching 1x exc target
                    advo=(h[fw]-ro) if d<0 else (ro-l[fw])
                    tgt=np.argmax(fav>=exc) if (fav>=exc).any() else len(fw)
                    mae=max(0,advo[:tgt+1].max()) if len(fw) else np.nan
                    rows.append(dict(sd=sd,d=d,exc_atr=exc/Aa,t=m[t],r05=reach(0.5),r1=reach(1.0),r2=reach(2.0),ext_retaken=first_ext<10**6,
                                     mae_exc=mae/exc,eod=(c[flat[t]]-c[t])*d/exc,close_t=c[t],ro=ro))
                    break
    return pd.DataFrame(rows)
for X in (0.1,0.15,0.25):
    for TEND in (600,630,660):
        R=study(X,TEND)
        if len(R)==0: continue
        print(f"X={X} ATR early move, re-cross by {TEND//60}:{TEND%60:02d}: days {len(R)} ({len(R)/248*100:.0f}% of days) | median exc {R.exc_atr.median():.2f} ATR | "
              f"P(+0.5x before extreme retaken) {R.r05.mean():.2f}  P(+1x) {R.r1.mean():.2f}  P(+2x) {R.r2.mean():.2f} | extreme retaken same day {R.ext_retaken.mean():.2f} | "
              f"MAE (beyond open, x exc) median {R.mae_exc.median():.2f} P75 {R.mae_exc.quantile(.75):.2f} | EOD move mean {R.eod.mean():+.2f}x exc")
