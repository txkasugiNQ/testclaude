import numpy as np
from numba import njit
@njit(cache=True)
def first_passage(h, l, c, tod, day, starts, up, dn, end_tod):
    """from close of 1m bar s: long outcome: +1 if hits c+up before c-dn (ambiguous bar -> -1), 0 none.
       short outcome similarly. returns also MFE/MAE (points) until end_tod for long."""
    n = len(starts)
    lo = np.zeros(n, np.int8); so = np.zeros(n, np.int8)
    mfe = np.zeros(n); mae = np.zeros(n)
    N = len(h)
    for k in range(n):
        s = starts[k]; e = c[s]; d = day[s]
        U = e + up[k]; D = e - dn[k]
        lres = 0; sres = 0
        hi = e; lw = e
        for i in range(s+1, N):
            if day[i] != d or tod[i] > end_tod: break
            if lres == 0:
                if l[i] <= D: lres = -1
                elif h[i] >= U: lres = 1
            # short: target e-dn... use symmetric: short wins if low <= e-up before high >= e+dn
            if sres == 0:
                if h[i] >= e + dn[k]: sres = -1
                elif l[i] <= e - up[k]: sres = 1
            hi = max(hi, h[i]); lw = min(lw, l[i])
            if lres != 0 and sres != 0: break
        lo[k] = lres; so[k] = sres; mfe[k] = hi - e; mae[k] = e - lw
    return lo, so, mfe, mae
