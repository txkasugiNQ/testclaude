"""Fixed SL / TP simulator (numba). No trailing, no BE.
Entry: market at OPEN of bar e. Per bar from e: (1) STOP first (gap beyond stop -> fill at open), (2) TP limit needs trade-through
(high >= tp + 1 tick for long) and fills at tp, (3) time exit decided at bar close (max bars / flat time / exit_tod) -> next open.
Trades whose entry open is already at/through stop or target are skipped. Daily +-limit on realised R; one position at a time."""
import numpy as np
from numba import njit
TICK = 0.25
@njit(cache=True)
def sim_fixed(o, h, l, c, sid, tod, e_arr, d_arr, sl_arr, tp_arr, maxbars, flat, dup, ddn):
    n = len(o); m = len(e_arr)
    res = np.full((m, 7), np.nan)   # taken, exit_idx, pnl_R, R_pts, bars, reason(1 SL,2 TP,3 time), mae
    busy = -1; cur = -1; dayR = 0.0
    for k in range(m):
        e = e_arr[k]; d = d_arr[k]
        res[k, 0] = 0.0
        if sid[e] != cur:
            cur = sid[e]; dayR = 0.0
        if e <= busy or dayR >= dup or dayR <= ddn: continue
        entry = o[e] * d; sl = sl_arr[k] * d; tp = tp_arr[k] * d
        R = entry - sl
        if R <= 0 or tp - entry <= 0: continue
        res[k, 0] = 1.0
        j = e; pnl = 0.0; reason = 0; mae = 0.0
        while True:
            if d > 0:
                oj, hj, lj, cj = o[j], h[j], l[j], c[j]
            else:
                oj, hj, lj, cj = -o[j], -l[j], -h[j], -c[j]
            mae = max(mae, (entry - lj) / R)
            if j > e and oj <= sl:
                pnl = (oj - entry) / R; reason = 1; break
            if lj <= sl:
                pnl = (sl - entry) / R; reason = 1; break
            if hj >= tp + TICK:
                pnl = (tp - entry) / R; reason = 2; break
            last = (j + 1 >= n) or (sid[j + 1] != sid[j])
            if (j - e + 1) >= maxbars or tod[j] >= flat or last:
                if last:
                    pnl = (cj - entry) / R
                else:
                    on = o[j + 1] * d; pnl = (on - entry) / R; j += 1
                reason = 3; break
            j += 1
        res[k, 1] = j; res[k, 2] = pnl; res[k, 3] = R; res[k, 4] = j - e + 1; res[k, 5] = reason; res[k, 6] = mae
        busy = j; dayR += pnl
    return res
