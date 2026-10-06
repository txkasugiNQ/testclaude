"""Independent slow reference implementation (plain python, written separately) to cross-check sim.simulate."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
TICK = 0.25
def ref_trade(e, d, stop0, P, o, h, l, c, atr, sid, tod):
    be_trig, be_off, ttype, tact, tdist, s2t, s2d, tp, pf, ptp, mb, flat = P[:12]
    entry = o[e]; R = (entry - stop0) * d; stop = stop0; best = entry; rem = 1.0; pnl = 0.0; pd_ = False
    j = e
    while True:
        fav = lambda p: (p - entry) * d          # signed profit in points
        hi_fav = fav(h[j]) if d > 0 else fav(l[j]); lo_fav = fav(l[j]) if d > 0 else fav(h[j])
        stop_fav = fav(stop)
        if j > e and fav(o[j]) <= stop_fav: return pnl + rem * fav(o[j]) / R, j
        if lo_fav <= stop_fav: return pnl + rem * stop_fav / R, j
        if pf > 0 and not pd_ and hi_fav >= ptp * R + TICK: pnl += pf * ptp; rem -= pf; pd_ = True
        if tp > 0 and hi_fav >= tp * R + TICK: return pnl + rem * tp, j
        best_fav = max(fav(best), hi_fav); best = entry + d * best_fav
        if j + 1 >= len(o) or sid[j + 1] != sid[j]:
            return pnl + rem * fav(c[j]) / R, j
        if j - e + 1 >= mb or tod[j] >= flat:
            return pnl + rem * fav(o[j + 1]) / R, j + 1
        m = best_fav / R
        new = stop_fav
        if be_trig > 0 and m >= be_trig: new = max(new, be_off * R)
        if ttype > 0 and m >= tact:
            if ttype == 1: cand = best_fav - tdist * R
            elif ttype == 2: cand = best_fav - tdist * atr[j]
            elif ttype == 3: cand = lo_fav - TICK
            else: cand = min((fav(l[q]) if d > 0 else fav(h[q])) for q in range(max(e, j - int(tdist) + 1), j + 1)) - TICK
            new = max(new, cand)
        if s2t > 0 and m >= s2t: new = max(new, best_fav - s2d * R)
        stop = entry + d * new
        j += 1
o, h, l, c, atr, sid, tod = ARR
E = setup_entries('H3', stop_floor_atr=2.0)
cfgs = [params(maxbars=60), params(tp=2), params(be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25),
        params(tr_type=4, tr_act=1.0, tr_dist=10), params(pfrac=0.5, ptp=1.0, be_trig=1.0, tp=3), params(tr_type=2, tr_act=1, tr_dist=3, s2_trig=2, s2_dist=0.5),
        params(tr_type=3, tr_act=0.5, be_trig=0.2)]
for P in cfgs:
    T = run(E, P)
    diffs = []
    for _, t in T.iterrows():
        pnl, xi = ref_trade(int(t.e), int(t.d), t.stop, P, o, h, l, c, atr, sid, tod)
        diffs.append((abs(pnl - t.pnl), xi - t.xi))
    dd = np.array(diffs)
    print('max |pnl diff|', dd[:, 0].max().round(6), 'exit idx mismatches', int((dd[:, 1] != 0).sum()), 'of', len(dd))
