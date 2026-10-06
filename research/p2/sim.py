"""Sequential trade simulator (numba). Identical logic is used by the Pine Script.

Per 1-min bar j of an open trade (prices transformed to 'long coordinates' for shorts):
 1) STOP (level set at previous bar close): gap -> fill at open; else if low<=stop -> fill at stop.  Checked FIRST.
 2) PARTIAL limit (if any): needs high >= level + 1 tick (trade-through), fill at level.
 3) FULL TARGET limit (if any): same trade-through rule.
 4) TIME exits decided at bar close (max bars, flat time 15:54 bar) -> filled at NEXT bar open; session-last bar -> its close.
 5) At bar close: update MFE / highest high -> BE / trailing levels for the NEXT bar (stop only ratchets).
Daily rule: realised day R >= +limit or <= -limit -> no NEW trades that day (an open trade keeps running).
One position at a time.
"""
import numpy as np
from numba import njit

TICK = 0.25
# param vector indices
P_BE_TRIG, P_BE_OFF, P_TR_TYPE, P_TR_ACT, P_TR_DIST, P_S2_TRIG, P_S2_DIST, P_TP, P_PFRAC, P_PTP, P_MAXBARS, P_FLAT, P_DUP, P_DDN = range(14)

def params(be_trig=0, be_off=0, tr_type=0, tr_act=0, tr_dist=0, s2_trig=0, s2_dist=0, tp=0, pfrac=0, ptp=0,
           maxbars=90, flat=15 * 60 + 54, dup=1.0, ddn=-1.0):
    return np.array([be_trig, be_off, tr_type, tr_act, tr_dist, s2_trig, s2_dist, tp, pfrac, ptp, maxbars, flat, dup, ddn], np.float64)

@njit(cache=True)
def simulate(o, h, l, c, atr, sid, tod, e_arr, d_arr, stop_arr, P):
    n = len(o); m = len(e_arr)
    res = np.full((m, 9), np.nan)   # taken, exit_idx, pnl_R, R_pts, mfe, mae, bars, reason, day_R_before
    busy_until = -1; cur_day = -1; day_R = 0.0
    be_trig, be_off, tr_type, tr_act, tr_dist = P[0], P[1], int(P[2]), P[3], P[4]
    s2_trig, s2_dist, tp, pfrac, ptp, maxbars, flat, dup, ddn = P[5], P[6], P[7], P[8], P[9], int(P[10]), P[11], P[12], P[13]
    for k in range(m):
        e = e_arr[k]; d = d_arr[k]
        if sid[e] != cur_day:
            cur_day = sid[e]; day_R = 0.0
        res[k, 0] = 0.0
        if e <= busy_until: continue
        if day_R >= dup or day_R <= ddn: continue
        entry = o[e] * d
        stop = stop_arr[k] * d
        R = entry - stop
        if R <= 0: continue
        res[k, 0] = 1.0; res[k, 8] = day_R
        hh = entry; mfe = 0.0; mae = 0.0
        remaining = 1.0; pnl = 0.0; pdone = False
        reason = 0; j = e; xi = e
        while True:
            if d > 0:
                oj, hj, lj, cj = o[j], h[j], l[j], c[j]
            else:
                oj, hj, lj, cj = -o[j], -l[j], -h[j], -c[j]
            exited = False
            # 1) stop
            if j > e and oj <= stop:
                pnl += remaining * (oj - entry) / R; exited = True; reason = 1
            elif lj <= stop:
                pnl += remaining * (stop - entry) / R; exited = True; reason = 1
            if not exited:
                # 2) partial
                if pfrac > 0 and not pdone and hj >= entry + ptp * R + TICK:
                    pnl += pfrac * ptp; remaining -= pfrac; pdone = True
                # 3) full target
                if tp > 0 and hj >= entry + tp * R + TICK:
                    pnl += remaining * tp; exited = True; reason = 2
            mae = max(mae, (entry - lj) / R)
            if not exited:
                hh = max(hh, hj); mfe = max(mfe, (hh - entry) / R)
                # 4) time exits at close
                last_bar = (j + 1 >= n) or (sid[j + 1] != sid[j])
                if (j - e + 1) >= maxbars or tod[j] >= flat or last_bar:
                    # market exit sent at this bar's close -> filled at NEXT bar open (Pine semantics)
                    if last_bar:
                        pnl += remaining * (cj - entry) / R
                    else:
                        on = o[j + 1] * d
                        pnl += remaining * (on - entry) / R
                        j += 1
                    exited = True; reason = 3
            if exited:
                xi = j; break
            # 5) management for next bar
            if be_trig > 0 and mfe >= be_trig:
                stop = max(stop, entry + be_off * R)
            if tr_type > 0 and mfe >= tr_act:
                if tr_type == 1:
                    cand = hh - tr_dist * R
                elif tr_type == 2:
                    cand = hh - tr_dist * atr[j]
                elif tr_type == 3:
                    cand = lj - TICK
                else:
                    nb = int(tr_dist); lo_ = lj
                    for q in range(max(e, j - nb + 1), j + 1):
                        v = l[q] if d > 0 else -h[q]
                        if v < lo_: lo_ = v
                    cand = lo_ - TICK
                stop = max(stop, cand)
            if s2_trig > 0 and mfe >= s2_trig:
                stop = max(stop, hh - s2_dist * R)
            j += 1
        res[k, 1] = xi; res[k, 2] = pnl; res[k, 3] = R; res[k, 4] = mfe; res[k, 5] = mae
        res[k, 6] = xi - e + 1; res[k, 7] = reason
        busy_until = xi
        day_R += pnl
    return res
