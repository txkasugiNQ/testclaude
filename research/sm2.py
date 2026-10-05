"""State machine with 1-minute execution and TF-bar (1/2/3m) setup logic, aggregated on the fly.
This is the exact logic of the Pine script (run on a 1m chart)."""
import numpy as np
from numba import njit

@njit(cache=True)
def _log(arrs, nt, pos, e_sig, e_bar, i, e_px, init_sl, tp, xpx, R, rsn, e_lvl, ext, worst):
    (t_side, t_sig, t_ent, t_ex, t_epx, t_sl, t_tp, t_xpx, t_R, t_mfe, t_mae, t_rsn, t_lvl) = arrs
    t_side[nt] = pos; t_sig[nt] = e_sig; t_ent[nt] = e_bar; t_ex[nt] = i; t_epx[nt] = e_px; t_sl[nt] = init_sl
    t_tp[nt] = tp; t_xpx[nt] = xpx; t_R[nt] = (xpx - e_px) * pos / R; t_rsn[nt] = rsn; t_lvl[nt] = e_lvl
    t_mfe[nt] = (ext - e_px) * pos / R; t_mae[nt] = (e_px - worst) * pos / R

@njit(cache=True)
def run_sm2(o, h, l, c, tod, day, regime, tf, atr_len,
            brk_start, brk_end, ent_end, flat_tod,
            a_pull, s_stop, wait_bars, cancel_atr, tp_R, max_trades,
            be_R, trail_start_R, trail_R, refresh, allow_long, allow_short, min_stop_pts,
            part_R, part_frac, stop_mode, swing_n, entry_mode, min_age, max_age, ts_bars, ts_minR, rth_open, adr, td_min):
    N = len(o)
    MAXT = 200000
    t_side = np.zeros(MAXT, np.int64); t_sig = np.zeros(MAXT, np.int64); t_ent = np.zeros(MAXT, np.int64); t_ex = np.zeros(MAXT, np.int64)
    t_epx = np.zeros(MAXT); t_sl = np.zeros(MAXT); t_tp = np.zeros(MAXT); t_xpx = np.zeros(MAXT); t_R = np.zeros(MAXT)
    t_mfe = np.zeros(MAXT); t_mae = np.zeros(MAXT); t_rsn = np.zeros(MAXT, np.int64); t_lvl = np.zeros(MAXT)
    arrs = (t_side, t_sig, t_ent, t_ex, t_epx, t_sl, t_tp, t_xpx, t_R, t_mfe, t_mae, t_rsn, t_lvl)
    nt = 0
    alpha = 1.0 / atr_len
    # TF aggregation state
    tf_o = 0.0; tf_h = -1e18; tf_l = 1e18; tf_c = 0.0; tf_prev_c = np.nan; tf_atr = np.nan; tf_bucket = -99999
    # swing history of TF bars (lows/highs) for structural stops
    SW = 64
    sw_h = np.full(SW, np.nan); sw_l = np.full(SW, np.nan); sw_k = 0
    cur_day = -1
    tfk = 0; h_set = 0; l_set = 0        # TF bar counter and bar index when session extremes were last set
    rth_h = -1e18; rth_l = 1e18          # RTH extreme as of last COMPLETED TF bar
    rth_h_run = -1e18; rth_l_run = 1e18  # running incl. current partial TF bar
    trades_today = 0
    pend = 0; p_side = 0; p_lim = 0.0; p_sl = 0.0; p_tp = 0.0; p_cancel = 0.0; p_bars = 0; p_sig = -1; p_lvl = 0.0
    pos = 0; e_px = 0.0; sl = 0.0; tp = 0.0; R = 0.0; ext = 0.0; worst = 0.0; e_bar = -1; first = False; init_sl = 0.0; e_sig = -1; e_lvl = 0.0
    part_done = False; realized = 0.0; rem = 1.0; part_px = 0.0
    for i in range(N):
        if day[i] != cur_day:
            cur_day = day[i]; rth_h = -1e18; rth_l = 1e18; rth_h_run = -1e18; rth_l_run = 1e18; tfk = 0; h_set = 0; l_set = 0
            trades_today = 0; pend = 0; pos = 0
        # ---- TF bucket for this 1m bar (bar close label tod): bucket id = ceil(tod/tf)
        bk = (tod[i] - 1) // tf if tod[i] > 0 else -((-tod[i]) // tf) - 1
        bk = int(np.floor((tod[i] - 1) / tf))
        if bk != tf_bucket:
            tf_bucket = bk; tf_o = o[i]; tf_h = h[i]; tf_l = l[i]
        else:
            if h[i] > tf_h: tf_h = h[i]
            if l[i] < tf_l: tf_l = l[i]
        tf_c = c[i]
        tf_close = (tod[i] % tf == 0) or (i + 1 >= N) or (day[i+1] != day[i])
        bopen_t = tod[i] - 1
        # ================= 1) manage open position on this 1m bar =================
        if pos != 0:
            exited = False; xpx = 0.0; rsn = 0
            if pos > 0:
                if (not first) and o[i] <= sl: xpx = o[i]; exited = True
                elif l[i] <= sl: xpx = sl; exited = True
                else:
                    hi_ok = c[i] if first else h[i]
                    if part_frac > 0 and not part_done and hi_ok >= part_px:
                        realized += part_frac * part_R; rem -= part_frac; part_done = True
                    if tp_R > 0 and hi_ok >= tp:
                        xpx = tp; exited = True; rsn = 2
            else:
                if (not first) and o[i] >= sl: xpx = o[i]; exited = True
                elif h[i] >= sl: xpx = sl; exited = True
                else:
                    lo_ok = c[i] if first else l[i]
                    if part_frac > 0 and not part_done and lo_ok <= part_px:
                        realized += part_frac * part_R; rem -= part_frac; part_done = True
                    if tp_R > 0 and lo_ok <= tp:
                        xpx = tp; exited = True; rsn = 2
            if exited and rsn == 0: rsn = 1 if sl == init_sl else 4
            if not exited:
                if pos > 0:
                    fav = c[i] if first else h[i]
                    if fav > ext: ext = fav
                    if l[i] < worst: worst = l[i]
                else:
                    fav = c[i] if first else l[i]
                    if fav < ext: ext = fav
                    if h[i] > worst: worst = h[i]
                if tod[i] >= flat_tod or i + 1 >= N or day[i+1] != day[i]:
                    xpx = c[i]; exited = True; rsn = 3
                elif ts_bars > 0 and (i - e_bar) >= ts_bars and (ext - e_px) * pos / R < ts_minR:
                    xpx = c[i]; exited = True; rsn = 5
            if exited:
                Rfull = (xpx - e_px) * pos / R
                _log(arrs, nt, pos, e_sig, e_bar, i, e_px, init_sl, tp, xpx, R, rsn, e_lvl, ext, worst)
                t_R[nt] = realized + rem * Rfull
                nt += 1; pos = 0
            else:
                mfeR = (ext - e_px) * pos / R
                if be_R > 0 and mfeR >= be_R:
                    nsl = e_px
                    if pos > 0 and nsl > sl: sl = nsl
                    if pos < 0 and nsl < sl: sl = nsl
                if part_frac > 0 and part_done and be_R < 0:
                    nsl = e_px
                    if pos > 0 and nsl > sl: sl = nsl
                    if pos < 0 and nsl < sl: sl = nsl
                if trail_R > 0 and mfeR >= trail_start_R:
                    nsl = ext - pos * trail_R * R
                    if pos > 0 and nsl > sl: sl = nsl
                    if pos < 0 and nsl < sl: sl = nsl
                first = False
        # ================= 2) pending order on this 1m bar =================
        elif pend != 0:
            filled = False; cancelled = False
            if bopen_t >= ent_end or tod[i] > flat_tod:
                cancelled = True
            elif entry_mode == 2:
                dist = abs(p_lim - p_sl)
                p_lim = o[i]; p_sl = o[i] - p_side * dist; p_tp = o[i] + p_side * tp_R * dist
                filled = True
            elif entry_mode == 1:
                if p_side > 0 and h[i] >= p_lim:
                    filled = True; p_lim = max(p_lim, o[i])
                elif p_side < 0 and l[i] <= p_lim:
                    filled = True; p_lim = min(p_lim, o[i])
            elif p_side > 0:
                if h[i] >= p_cancel: cancelled = True
                elif l[i] <= p_lim - 0.25: filled = True
            else:
                if l[i] <= p_cancel: cancelled = True
                elif h[i] >= p_lim + 0.25: filled = True
            if filled:
                pos = p_side; e_px = p_lim; sl = p_sl; init_sl = p_sl; tp = p_tp; R = abs(e_px - sl); e_bar = i; e_sig = p_sig; e_lvl = p_lvl
                if entry_mode == 1:
                    tp = e_px + pos * tp_R * abs(e_px - sl)
                ext = e_px; worst = e_px; first = True; pend = 0; trades_today += 1
                part_done = False; realized = 0.0; rem = 1.0; part_px = e_px + pos * part_R * R
                exited = False; xpx = 0.0; rsn = 0
                if pos > 0:
                    if l[i] <= sl: xpx = sl; exited = True; rsn = 1
                    else:
                        if part_frac > 0 and c[i] >= part_px:
                            realized += part_frac * part_R; rem -= part_frac; part_done = True
                        if tp_R > 0 and c[i] >= tp: xpx = tp; exited = True; rsn = 2
                        else: worst = min(worst, l[i]); ext = max(ext, c[i])
                else:
                    if h[i] >= sl: xpx = sl; exited = True; rsn = 1
                    else:
                        if part_frac > 0 and c[i] <= part_px:
                            realized += part_frac * part_R; rem -= part_frac; part_done = True
                        if tp_R > 0 and c[i] <= tp: xpx = tp; exited = True; rsn = 2
                        else: worst = max(worst, h[i]); ext = min(ext, c[i])
                if not exited and (tod[i] >= flat_tod or i + 1 >= N or day[i+1] != day[i]):
                    xpx = c[i]; exited = True; rsn = 3
                if exited:
                    Rfull = (xpx - e_px) * pos / R
                    _log(arrs, nt, pos, e_sig, e_bar, i, e_px, init_sl, tp, xpx, R, rsn, e_lvl, ext, worst)
                    t_R[nt] = realized + rem * Rfull
                    nt += 1; pos = 0
                else:
                    first = False
                    mfeR = (ext - e_px) * pos / R
                    if be_R > 0 and mfeR >= be_R:
                        nsl = e_px
                        if pos > 0 and nsl > sl: sl = nsl
                        if pos < 0 and nsl < sl: sl = nsl
                    if part_frac > 0 and part_done and be_R < 0:
                        nsl = e_px
                        if pos > 0 and nsl > sl: sl = nsl
                        if pos < 0 and nsl < sl: sl = nsl
                    if trail_R > 0 and mfeR >= trail_start_R:
                        nsl = ext - pos * trail_R * R
                        if pos > 0 and nsl > sl: sl = nsl
                        if pos < 0 and nsl < sl: sl = nsl
            elif cancelled:
                pend = 0
        # ================= 3) TF bar close: update ATR, detect setup =================
        if tf_close:
            # TF ATR (Wilder RMA of true range)
            if np.isnan(tf_prev_c): tr = tf_h - tf_l
            else: tr = max(tf_h - tf_l, abs(tf_h - tf_prev_c), abs(tf_l - tf_prev_c))
            tf_atr = tr if np.isnan(tf_atr) else tf_atr + alpha * (tr - tf_atr)
            tf_prev_c = tf_c
            sw_h[sw_k % SW] = tf_h; sw_l[sw_k % SW] = tf_l; sw_k += 1
            # pending order lifetime counts TF bars
            if pend != 0:
                p_bars -= 1
                if p_bars <= 0: pend = 0
            is_rth = tod[i] > 570
            new_hi = is_rth and rth_h > -1e17 and tf_h > rth_h
            new_lo = is_rth and rth_l < 1e17 and tf_l < rth_l
            prev_h = rth_h; prev_l = rth_l
            age_h_prev = tfk - h_set; age_l_prev = tfk - l_set   # age of the level BEFORE this bar
            if is_rth:
                if tf_h > rth_h: rth_h = tf_h; h_set = tfk
                if tf_l < rth_l: rth_l = tf_l; l_set = tfk
            age_h = tfk - h_set; age_l = tfk - l_set
            tfk += 1
            if pos == 0 and trades_today < max_trades and tod[i] >= brk_start and tod[i] <= brk_end:
                if entry_mode == 1:
                    pend = 0
                for sd in (1, -1):
                    if td_min > -900 and (np.isnan(adr[i]) or np.isnan(rth_open[i]) or (tf_c - rth_open[i]) * sd < td_min * adr[i]): continue
                    if entry_mode == 2:
                        if sd > 0 and not (allow_long and regime[i] > 0): continue
                        if sd < 0 and not (allow_short and regime[i] < 0): continue
                        if pend != 0: continue
                        lvl = tf_c; lim = tf_c
                    elif entry_mode == 1:
                        if sd > 0 and not (allow_long and regime[i] > 0): continue
                        if sd < 0 and not (allow_short and regime[i] < 0): continue
                        ag = age_h if sd > 0 else age_l
                        if ag < min_age or ag > max_age: continue
                        lvl = rth_h if sd > 0 else rth_l
                        lim = lvl + sd * 0.25
                    else:
                        if sd > 0 and not (allow_long and regime[i] > 0 and new_hi): continue
                        if sd < 0 and not (allow_short and regime[i] < 0 and new_lo): continue
                        if pend != 0 and not refresh and p_side == sd: continue
                        ag = age_h_prev if sd > 0 else age_l_prev
                        if ag < min_age or ag > max_age: continue
                        lvl = prev_h if sd > 0 else prev_l
                        lim = lvl - sd * a_pull * tf_atr
                    if stop_mode == 0:
                        stp = lim - sd * s_stop * tf_atr
                    else:
                        # structural: lowest low (highest high) of last swing_n TF bars incl. current, minus buffer
                        ex_ = 1e18 if sd > 0 else -1e18
                        for j in range(swing_n):
                            kk = (sw_k - 1 - j) % SW
                            if sd > 0: ex_ = min(ex_, sw_l[kk])
                            else: ex_ = max(ex_, sw_h[kk])
                        stp = ex_ - sd * s_stop * tf_atr
                    if (lim - stp) * sd < min_stop_pts:
                        stp = lim - sd * min_stop_pts
                    if entry_mode == 0 and (tf_c - lim) * sd <= 0.25: continue
                    if entry_mode == 1 and pend != 0: continue
                    if entry_mode == 2: wb = 1
                    pend = sd; p_side = sd; p_lim = lim; p_sl = stp; p_tp = lim + sd * tp_R * abs(lim - stp)
                    p_cancel = (tf_h if sd > 0 else tf_l) + sd * cancel_atr * tf_atr
                    p_bars = wait_bars; p_sig = i; p_lvl = lvl
    return arrs, nt
