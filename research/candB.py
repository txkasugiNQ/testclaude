"""Candidate B: after a breakout to a new session extreme (trend-aligned, early PM), buy the pullback with a limit."""
from cand import *
def signals_B(b, a=0.5, s_atr=1.0, w=50, kind='ma', win=(720,840), wait=10, conf='touch', stop_mode='atr'):
    S = pd.Series; day=b.day; tod=b.tod; c,h,l,atr = b.c,b.h,b.l,b.atr
    L = daylevels(b)
    reg = daily_regime(b, w, kind)
    prh = S(L['rh']).groupby(day).shift(1).values; prl = S(L['rl']).groupby(day).shift(1).values
    rows=[]
    ok = (tod >= win[0]) & (tod <= win[1]) & np.isfinite(reg)
    for side in (1,-1):
        if side>0:
            brk = ok & (reg==1) & (h > prh) if conf=='touch' else ok & (reg==1) & (c > prh)
        else:
            brk = ok & (reg==-1) & (l < prl) if conf=='touch' else ok & (reg==-1) & (c < prl)
        idx = np.where(brk)[0]
        X = prh[idx] if side>0 else prl[idx]          # the level that was broken
        ext = h[idx] if side>0 else l[idx]             # new extreme so far
        e = X - side*a*atr[idx]                         # limit below broken level by a*ATR (a can be negative => above)
        if stop_mode == 'atr': sl = e - side*s_atr*atr[idx]
        d_ = pd.DataFrame(dict(sb=idx, side=side, etype=2, eprice=e, sl=sl, expiry=wait, cancel=ext + side*2*atr[idx]))
        d_ = d_[(c[idx] - e)*side > 0.25]     # limit must be non-marketable at placement
        rows.append(d_)
    s = pd.concat(rows)
    return s
