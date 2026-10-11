"""Raw event extraction (one pass per structural setting); SL/TP variants are applied afterwards (vectorised)."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from events import ctx, days, rnd, TICK

def sweep_raw(rs=8*60+12, re=9*60+12, win_end=11*60, N=10, min_depth=0.0, max_depth=1.0):
    """REVERSAL raw events: beyond-edge excursion then close back inside within N bars. Returns sweep extreme etc."""
    c = ctx(); df = c['df']; H, L, C, T = (df[k].values for k in ('high', 'low', 'close', 'tod'))
    rows = []
    for r, a in days(rs, re):
        hi, lo = H[r].max(), L[r].min(); size = hi - lo
        if size <= 0: continue
        for side in (1, -1):
            st = None
            for p, i in enumerate(a):
                if T[i] >= win_end: break
                if st is None:
                    if (H[i] > hi) if side > 0 else (L[i] < lo): st = [p, H[i] if side > 0 else L[i]]
                    else: continue
                st[1] = max(st[1], H[i]) if side > 0 else min(st[1], L[i])
                depth = (st[1] - hi) / size if side > 0 else (lo - st[1]) / size
                if depth > max_depth or p - st[0] > N: break          # first sweep per side only
                if ((C[i] < hi) if side > 0 else (C[i] > lo)) and depth >= min_depth:
                    rows.append((i + 1, -side, st[1], hi, lo, size, C[i], depth)); break
    return pd.DataFrame(rows, columns=['e', 'd', 'ext', 'hi', 'lo', 'size', 'sigc', 'depth'])

def breakout_raw(rs=8*60+12, re=9*60+12, win_end=11*60, retest=False):
    c = ctx(); df = c['df']; H, L, C, T = (df[k].values for k in ('high', 'low', 'close', 'tod'))
    rows = []
    for r, a in days(rs, re):
        hi, lo = H[r].max(), L[r].min(); size = hi - lo
        if size <= 0: continue
        for side in (1, -1):
            state = 0
            for i in a:
                if T[i] >= win_end: break
                cb = C[i] > hi if side > 0 else C[i] < lo
                if not retest and cb:
                    rows.append((i + 1, side, H[i] if side > 0 else L[i], hi, lo, size, C[i], L[i] if side > 0 else H[i])); break
                if retest:
                    if state == 0 and cb: state = 1; continue
                    if state == 1 and ((L[i] <= hi) if side > 0 else (H[i] >= lo)) and cb:
                        rows.append((i + 1, side, H[i] if side > 0 else L[i], hi, lo, size, C[i], L[i] if side > 0 else H[i])); break
    return pd.DataFrame(rows, columns=['e', 'd', 'barext', 'hi', 'lo', 'size', 'sigc', 'barlow'])

def apply_rev(R, sl_buf, tp_mode, tp_val):
    d = R.d.values; size = R['size'].values
    sl = R.ext.values - d * sl_buf * size              # beyond the sweep extreme (d=-1 for upper sweep -> sl above)
    sl = np.where(d > 0, np.floor(sl / TICK) * TICK, np.ceil(sl / TICK) * TICK)
    Rr = np.abs(R.sigc.values - sl)
    if tp_mode == 'mid': tp = (R.hi.values + R.lo.values) / 2
    elif tp_mode == 'opp': tp = np.where(d < 0, R.lo.values, R.hi.values)
    else: tp = R.sigc.values + d * tp_val * Rr
    tp = np.where(d > 0, np.floor(tp / TICK) * TICK, np.ceil(tp / TICK) * TICK)
    return pd.DataFrame({'e': R.e.values, 'd': d, 'sl': sl, 'tp': tp, 'size': size})

def apply_brk(R, sl_mode, sl_val, tp_mode, tp_val):
    d = R.d.values; size = R['size'].values; edge = np.where(d > 0, R.hi.values, R.lo.values)
    if sl_mode == 'mid': sl = (R.hi.values + R.lo.values) / 2
    elif sl_mode == 'in': sl = edge - d * sl_val * size
    else: sl = R.barlow.values - d * sl_val * size
    sl = np.where(d > 0, np.floor(sl / TICK) * TICK, np.ceil(sl / TICK) * TICK)
    Rr = np.abs(R.sigc.values - sl)
    tp = R.sigc.values + d * (tp_val * Rr if tp_mode == 'R' else tp_val * size)
    tp = np.where(d > 0, np.floor(tp / TICK) * TICK, np.ceil(tp / TICK) * TICK)
    return pd.DataFrame({'e': R.e.values, 'd': d, 'sl': sl, 'tp': tp, 'size': size})
