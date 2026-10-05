"""Conservative bar-based backtest engine.
Rules (no lookahead):
 - signals are known at the CLOSE of bar `sb`; orders are live from bar sb+1.
 - market: fill at open of sb+1. stop: fill when price trades AT/through level (fill = max(level, open) for long).
   limit: fill only when price trades THROUGH level by >=1 tick (low <= level-0.25 for long); fill = min(level, open).
 - in the fill bar: stop considered hit if bar extreme touches SL (worst case). TP in fill bar only when provably after fill.
 - later bars: gap through stop -> fill at open; SL and TP same bar -> SL (worst case).
 - stop modifications (BE/trailing) computed at bar close, effective from next bar.
 - entries only if fill bar opens at/after ent_start and fill happens before ent_end (bar close <= ent_end).
"""
import numpy as np
from numba import njit

TICK = 0.25

@njit(cache=True)
def simulate(o,h,l,c,tod,day,tf, sb, side, etype, eprice, slp, tpp, cancelp, expiry,
             ent_start, ent_end, flat_tod, be_R, be_lock_R, trail_start_R, trail_mode, trail_param,
             part_R, part_frac, max_bars, max_per_day, atr):
    n = len(sb)
    # outputs
    res = np.full(n, np.nan); mfe = np.full(n, np.nan); mae = np.full(n, np.nan)
    ent_bar = np.full(n, -1); ex_bar = np.full(n, -1); ent_px = np.full(n, np.nan); ex_px = np.full(n, np.nan)
    risk = np.full(n, np.nan); reason = np.zeros(n, np.int64)  # 1 SL,2 TP,3 time,4 trail/BE stop,5 cancel/expire
    busy_until = -1
    last_day = -1; cnt_day = 0
    N = len(o)
    for k in range(n):
        s = sb[k]
        if s < busy_until: continue
        d = day[s]
        if d != last_day:
            last_day = d; cnt_day = 0
        if cnt_day >= max_per_day: continue
        sd = side[k]
        # ---- find fill
        filled = -1; fpx = 0.0
        for i in range(s+1, min(s+1+expiry[k], N)):
            if day[i] != d: break
            bopen = tod[i] - tf
            if bopen < ent_start: continue
            if tod[i] > ent_end: break
            if etype[k] == 0:
                filled = i; fpx = o[i]; break
            elif etype[k] == 1:  # stop entry
                if sd > 0:
                    if not np.isnan(cancelp[k]) and l[i] <= cancelp[k] and h[i] < eprice[k]:
                        break
                    if h[i] >= eprice[k]:
                        filled = i; fpx = max(eprice[k], o[i]); break
                else:
                    if not np.isnan(cancelp[k]) and h[i] >= cancelp[k] and l[i] > eprice[k]:
                        break
                    if l[i] <= eprice[k]:
                        filled = i; fpx = min(eprice[k], o[i]); break
            else:  # limit entry (must trade through by a tick)
                if sd > 0:
                    if not np.isnan(cancelp[k]) and h[i] >= cancelp[k]:
                        break
                    if l[i] <= eprice[k] - TICK:
                        filled = i; fpx = eprice[k]; break
                else:
                    if not np.isnan(cancelp[k]) and l[i] <= cancelp[k]:
                        break
                    if h[i] >= eprice[k] + TICK:
                        filled = i; fpx = eprice[k]; break
        if filled < 0:
            reason[k] = 5
            continue
        R = (fpx - slp[k]) * sd
        if R <= 0:
            reason[k] = 5; continue
        cnt_day += 1
        stop = slp[k]; tp = tpp[k]
        hasTP = not np.isnan(tp)
        ext = fpx  # best price reached (favorable extreme)
        worst = fpx
        part_done = False; realized = 0.0; remaining = 1.0
        part_px = fpx + sd * part_R * R if part_frac > 0 else np.nan
        i = filled
        exitpx = np.nan; rsn = 0; exit_i = -1
        first = True
        while True:
            # ---------- exits on bar i
            if sd > 0:
                if not first and o[i] <= stop:
                    exitpx = o[i]; rsn = 1 if stop == slp[k] else 4; exit_i = i; break
                if l[i] <= stop:
                    exitpx = stop; rsn = 1 if stop == slp[k] else 4; exit_i = i; break
                # partial
                if part_frac > 0 and not part_done:
                    ok = h[i] >= part_px if (not first or etype[k] != 2) else c[i] >= part_px
                    if ok:
                        realized += part_frac * part_R; remaining -= part_frac; part_done = True
                if hasTP:
                    ok = h[i] >= tp if (not first or etype[k] != 2) else c[i] >= tp
                    if ok:
                        exitpx = max(tp, o[i]) if not first else tp; rsn = 2; exit_i = i; break
            else:
                if not first and o[i] >= stop:
                    exitpx = o[i]; rsn = 1 if stop == slp[k] else 4; exit_i = i; break
                if h[i] >= stop:
                    exitpx = stop; rsn = 1 if stop == slp[k] else 4; exit_i = i; break
                if part_frac > 0 and not part_done:
                    ok = l[i] <= part_px if (not first or etype[k] != 2) else c[i] <= part_px
                    if ok:
                        realized += part_frac * part_R; remaining -= part_frac; part_done = True
                if hasTP:
                    ok = l[i] <= tp if (not first or etype[k] != 2) else c[i] <= tp
                    if ok:
                        exitpx = min(tp, o[i]) if not first else tp; rsn = 2; exit_i = i; break
            # ---------- update extremes
            if sd > 0:
                hi_ = h[i] if (not first or etype[k] != 2) else c[i]
                ext = max(ext, hi_); worst = min(worst, l[i])
            else:
                lo_ = l[i] if (not first or etype[k] != 2) else c[i]
                ext = min(ext, lo_); worst = max(worst, h[i])
            # ---------- time exit at close
            if tod[i] >= flat_tod or (i - filled + 1) >= max_bars or i + 1 >= N or day[i+1] != d:
                exitpx = c[i]; rsn = 3; exit_i = i; break
            # ---------- stop management at close (effective next bar)
            mfeR = (ext - fpx) * sd / R
            if be_R > 0 and mfeR >= be_R:
                nst = fpx + sd * be_lock_R * R
                stop = max(stop, nst) if sd > 0 else min(stop, nst)
            if part_done and part_frac > 0 and be_R < 0:   # be_R<0 => BE after partial
                nst = fpx + sd * be_lock_R * R
                stop = max(stop, nst) if sd > 0 else min(stop, nst)
            if trail_mode > 0 and mfeR >= trail_start_R:
                if trail_mode == 1:     # distance in R from favorable extreme
                    nst = ext - sd * trail_param * R
                elif trail_mode == 2:   # lowest low / highest high of last k bars (incl current)
                    kk = int(trail_param)
                    if sd > 0:
                        nst = l[i]
                        for j in range(max(filled, i-kk+1), i+1): nst = min(nst, l[j])
                    else:
                        nst = h[i]
                        for j in range(max(filled, i-kk+1), i+1): nst = max(nst, h[j])
                elif trail_mode == 3:   # ATR multiple from extreme
                    nst = ext - sd * trail_param * atr[i]
                else:                   # trail_mode 4: distance in points
                    nst = ext - sd * trail_param
                stop = max(stop, nst) if sd > 0 else min(stop, nst)
            first = False
            i += 1
        pnl = (exitpx - fpx) * sd / R
        total = realized + remaining * pnl
        res[k] = total; ent_bar[k] = filled; ex_bar[k] = exit_i; ent_px[k] = fpx; ex_px[k] = exitpx
        risk[k] = R; reason[k] = rsn
        mfe[k] = (ext - fpx) * sd / R; mae[k] = (fpx - worst) * sd / R
        busy_until = exit_i
        # allow a new signal only after exit bar closes
    return res, mfe, mae, ent_bar, ex_bar, ent_px, ex_px, risk, reason
