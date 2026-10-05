import numpy as np
from numba import njit
@njit(cache=True)
def path_stats(h, l, c, tod, day, ent_i, side, epx, unit, ks, end_tod):
    """for each trade: ignoring any stop, from entry bar (inclusive, conservative: entry-bar adverse counts) to end_tod:
       mae_before[k] = max adverse (in units) before first reaching +k units (nan if never)
       mfe_total = max favorable to end_tod, mae_total = max adverse to end_tod, final = close at end in units
       t_reach[k] = minutes to reach +k"""
    n = len(ent_i); K = len(ks)
    mae_b = np.full((n, K), np.nan); t_r = np.full((n, K), np.nan)
    mfe_t = np.zeros(n); mae_t = np.zeros(n); fin = np.zeros(n)
    for j in range(n):
        i0 = ent_i[j]; d = day[i0]; s = side[j]; e = epx[j]; u = unit[j]
        mx = 0.0; mn = 0.0
        i = i0
        while i < len(h) and day[i] == d and tod[i] <= end_tod:
            fav = ((h[i] - e) if s > 0 else (e - l[i])) / u
            adv = ((e - l[i]) if s > 0 else (h[i] - e)) / u
            if i == i0:
                fav = ((c[i] - e) if s > 0 else (e - c[i])) / u  # conservative: only close counts as favorable in entry bar
            # adverse first (conservative ordering within bar)
            if adv > mn: mn = adv
            if fav > mx:
                for k in range(K):
                    if np.isnan(mae_b[j, k]) and fav >= ks[k]:
                        mae_b[j, k] = mn; t_r[j, k] = i - i0
                mx = fav
            fin[j] = ((c[i] - e) if s > 0 else (e - c[i])) / u
            i += 1
        mfe_t[j] = mx; mae_t[j] = mn
    return mae_b, t_r, mfe_t, mae_t, fin
