"""Forward outcome measurement for events. Everything starts AFTER the event bar closes (bar t+1 onward)."""
import numpy as np
from numba import njit

@njit(cache=True)
def first_passage(h, l, c, day, ev_bar, ev_level, ev_dir, X, H, same_day):
    """Barrier race measured from the LEVEL price: +1 if price reaches level+dir*X first ("reaction" in dir),
    -1 if it reaches level-dir*X first, 0 if both inside one bar (ambiguous), 9 if neither within H bars.
    Bars t+1..t+H. X is an array (per event) of distances."""
    n = len(ev_bar)
    res = np.full(n, 9, np.int8); tt = np.full(n, -1, np.int32)
    N = len(c)
    for k in range(n):
        t = ev_bar[k]; L = ev_level[k]; d = ev_dir[k]; x = X[k]
        up = L + d * x; dn = L - d * x
        for i in range(t + 1, min(t + 1 + H, N)):
            if same_day and day[i] != day[t]:
                break
            if d == 1:
                a = h[i] >= up; bb = l[i] <= dn
            else:
                a = l[i] <= up; bb = h[i] >= dn
            if a and bb:
                res[k] = 0; tt[k] = i - t; break
            if a:
                res[k] = 1; tt[k] = i - t; break
            if bb:
                res[k] = -1; tt[k] = i - t; break
    return res, tt

@njit(cache=True)
def mfe_mae(h, l, c, ev_bar, ev_dir, ref, H):
    """Max favourable / adverse excursion in direction dir, relative to price ref, over bars t+1..t+H."""
    n = len(ev_bar); N = len(c)
    mfe = np.full(n, np.nan); mae = np.full(n, np.nan); ret = np.full(n, np.nan)
    for k in range(n):
        t = ev_bar[k]; d = ev_dir[k]; r = ref[k]
        if t + H >= N:
            continue
        fa = 0.0; ad = 0.0
        for i in range(t + 1, t + H + 1):
            if d == 1:
                fa = max(fa, h[i] - r); ad = max(ad, r - l[i])
            else:
                fa = max(fa, r - l[i]); ad = max(ad, h[i] - r)
        mfe[k] = fa; mae[k] = ad; ret[k] = (c[t + H] - r) * d
    return mfe, mae, ret


@njit(cache=True)
def fixed_r(o, h, l, c, day, ev_bar, d_, stop_, ks, H, flat_smod, smod):
    """Entry = OPEN of bar t+1 (market order after the signal bar closed). Stop = stop_ (structural).
    For each target k (in R): +k if target reached before stop, -1 if stop first. CONSERVATIVE:
    stop and target inside the same bar -> loss; entry bar: stop touched -> loss, target only counts
    if the stop was not touched in that bar. Not resolved within H bars or session end (flat_mod) ->
    exit at that bar's close (R = actual). Returns R matrix, risk pts, mfeR, maeR (over H)."""
    n = len(ev_bar); K = len(ks); N = len(c)
    R = np.full((n, K), np.nan); risk = np.full(n, np.nan)
    mfe = np.full(n, np.nan); mae = np.full(n, np.nan); tbar = np.full((n, K), -1, np.int32)
    for k in range(n):
        t = ev_bar[k]; d = d_[k]
        if t + 2 >= N or day[t + 1] != day[t] or smod[t + 1] >= flat_smod:
            continue
        e = o[t + 1]; s = stop_[k]
        rk = (e - s) * d
        if rk <= 0:
            continue
        risk[k] = rk
        fa = 0.0; ad = 0.0
        done = np.zeros(K, np.bool_)
        last = t + 1
        for i in range(t + 1, min(t + 1 + H, N)):
            if day[i] != day[t] or smod[i] >= flat_smod:
                break
            last = i
            fav = (h[i] - e) if d == 1 else (e - l[i])
            adv = (e - l[i]) if d == 1 else (h[i] - e)
            stop_hit = adv >= rk
            for q in range(K):
                if done[q]:
                    continue
                tgt = fav >= ks[q] * rk
                if stop_hit:
                    R[k, q] = -1.0; done[q] = True; tbar[k, q] = i - t
                elif tgt:
                    R[k, q] = ks[q]; done[q] = True; tbar[k, q] = i - t
            if not stop_hit:
                fa = max(fa, fav)
            ad = max(ad, min(adv, rk))
            if stop_hit:
                break
        for q in range(K):
            if not done[q]:
                R[k, q] = (c[last] - e) * d / rk; tbar[k, q] = last - t
        mfe[k] = fa / rk; mae[k] = ad / rk
    return R, risk, mfe, mae, tbar
