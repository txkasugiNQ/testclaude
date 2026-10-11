"""Signal generation around the 08:12-09:12 ET range (bar START times). No look-ahead: every decision uses closed bars only.
Each function returns rows: e (entry bar idx = signal+1), d, sl, tp (absolute prices)."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'p3')); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'p2'))
from slots import ctx
from simfixed import sim_fixed, TICK
_D = {}
def days(rs=8 * 60 + 12, re=9 * 60 + 12, end=15 * 60 + 54):
    key = (rs, re, end)
    if key in _D: return _D[key]
    c = ctx(); df = c['df']; out = []
    gi = np.arange(len(df)); good = df.good.values; tod = df.tod.values; sid = df.sid.values
    for s, idx in pd.Series(gi[good]).groupby(sid[good]):
        idx = idx.values; t = tod[idx]
        r = idx[(t >= rs) & (t < re)]; a = idx[(t >= re) & (t <= end)]
        if len(r) < (re - rs) * 0.8 or len(a) < 100: continue
        out.append((r, a))
    _D[key] = out; return out

def rnd(x, d, away=True):
    """round stop away from entry (long: down), target toward entry (conservative)"""
    return np.floor(x / TICK) * TICK if (d > 0) == away else np.ceil(x / TICK) * TICK

def tp_price(entry_ref, d, sl, hi, lo, size, tp_mode, tp_val):
    R = abs(entry_ref - sl)
    if tp_mode == 'R': t = entry_ref + d * tp_val * R
    elif tp_mode == 'mid': t = (hi + lo) / 2
    elif tp_mode == 'opp': t = lo if d < 0 else hi
    elif tp_mode == 'edge': t = None
    elif tp_mode == 'size': t = entry_ref + d * tp_val * size
    return t

def sweep_reclaim(rs=8*60+12, re=9*60+12, win_end=11*60, N=10, min_depth=0.0, max_depth=1.0, sl_buf=0.05, tp_mode='mid', tp_val=1.0,
                  max_per_side=1, end=15*60+54):
    """REVERSAL: price trades beyond an edge (depth >= min_depth*size, never beyond max_depth*size while armed), then within N bars
    a 1m CLOSE back inside the range -> fade toward the range. SL = sweep extreme + sl_buf*size. TP: mid / opposite edge / R multiple."""
    c = ctx(); df = c['df']; O, H, L, C, T = (df[k].values for k in ('open', 'high', 'low', 'close', 'tod'))
    rows = []
    for r, a in days(rs, re, end):
        hi, lo = H[r].max(), L[r].min(); size = hi - lo
        if size <= 0: continue
        used = {1: 0, -1: 0}
        armed = {1: None, -1: None}   # side +1 = sweep above high -> short ; holds (start bar pos, extreme)
        for p, i in enumerate(a):
            if T[i] >= win_end: break
            for side in (1, -1):
                beyond = (H[i] - hi) if side > 0 else (lo - L[i])
                if armed[side] is None:
                    if beyond > 0 and used[side] < max_per_side:
                        armed[side] = [p, H[i] if side > 0 else L[i]]
                st = armed[side]
                if st is None: continue
                st[1] = max(st[1], H[i]) if side > 0 else min(st[1], L[i])
                depth = (st[1] - hi) / size if side > 0 else (lo - st[1]) / size
                if depth > max_depth or p - st[0] > N:
                    armed[side] = None; used[side] += 1; continue
                back_in = C[i] < hi if side > 0 else C[i] > lo
                if back_in and depth >= min_depth:
                    d = -side
                    sl = st[1] + side * sl_buf * size
                    sl = rnd(sl, d)
                    ref = C[i]
                    t = tp_price(ref, d, sl, hi, lo, size, tp_mode, tp_val)
                    rows.append((i + 1, d, sl, rnd(t, d, away=False), size))
                    armed[side] = None; used[side] += 1
    return pd.DataFrame(rows, columns=['e', 'd', 'sl', 'tp', 'size'])

def breakout(rs=8*60+12, re=9*60+12, win_end=11*60, sl_mode='mid', sl_val=0.5, tp_mode='R', tp_val=1.0, max_per_side=1, end=15*60+54, retest=False):
    """CONTINUATION: first 1m close beyond an edge -> enter (or with retest=True: after that close, wait for a bar touching the edge
    and closing back beyond it). SL: 'mid' range midpoint, 'in' = edge - sl_val*size (inside), TP: R multiple or size multiple."""
    c = ctx(); df = c['df']; O, H, L, C, T = (df[k].values for k in ('open', 'high', 'low', 'close', 'tod'))
    rows = []
    for r, a in days(rs, re, end):
        hi, lo = H[r].max(), L[r].min(); size = hi - lo
        if size <= 0: continue
        used = {1: 0, -1: 0}; state = {1: 0, -1: 0}
        for i in a:
            if T[i] >= win_end: break
            for side in (1, -1):
                if used[side] >= max_per_side: continue
                edge = hi if side > 0 else lo
                cb = C[i] > hi if side > 0 else C[i] < lo
                fire = False
                if not retest:
                    fire = cb
                else:
                    if state[side] == 0 and cb: state[side] = 1; continue
                    if state[side] == 1:
                        touched = L[i] <= hi if side > 0 else H[i] >= lo
                        if touched and cb: fire = True
                if fire:
                    d = side
                    if sl_mode == 'mid': sl = (hi + lo) / 2
                    elif sl_mode == 'in': sl = edge - d * sl_val * size
                    elif sl_mode == 'bar': sl = (L[i] if d > 0 else H[i]) - d * sl_val * size
                    sl = rnd(sl, d)
                    t = tp_price(C[i], d, sl, hi, lo, size, tp_mode, tp_val)
                    rows.append((i + 1, d, sl, rnd(t, d, away=False), size)); used[side] += 1
    return pd.DataFrame(rows, columns=['e', 'd', 'sl', 'tp', 'size'])

def run(E, maxbars=1000, flat=15 * 60 + 54, dup=1.0, ddn=-1.0, cost_pts=0.6):
    c = ctx(); df = c['df']
    if len(E) == 0: return pd.DataFrame()
    E = E.sort_values('e', kind='mergesort').reset_index(drop=True)
    arr = [df[k].values.astype(np.float64) for k in ('open', 'high', 'low', 'close')]
    r = sim_fixed(*arr, df.sid.values.astype(np.int64), df.tod.values.astype(np.float64), E.e.values.astype(np.int64), E.d.values.astype(np.int64),
                  E.sl.values.astype(np.float64), E.tp.values.astype(np.float64), maxbars, flat, dup, ddn)
    T = E.copy(); T['taken'] = r[:, 0] == 1; T['xi'] = r[:, 1]; T['pnl'] = r[:, 2]; T['Rpts'] = r[:, 3]; T['bars'] = r[:, 4]; T['reason'] = r[:, 5]; T['mae'] = r[:, 6]
    T = T[T.taken].copy(); T['pnl_net'] = T.pnl - cost_pts / T.Rpts
    T['sess'] = df.sess.values[T.e.values]; T['yr'] = c['YR'][T.e.values]; T['etod'] = df.tod.values[T.e.values]
    return T

def summarize(T, ndays=730):
    if len(T) == 0: return {'n/day': 0}
    x = T.pnl.values; w = x > 1e-9; l = x < -1e-9
    srt = np.sort(x)[::-1]; k = max(1, int(round(0.05 * len(x))))
    r = {'n/day': len(x) / ndays, 'WR': w.mean(), 'avgW': x[w].mean() if w.any() else 0, 'avgL': x[l].mean() if l.any() else 0,
         'exp': x.mean(), 'net': T.pnl_net.mean(), 'PF': x[w].sum() / -x[l].sum() if l.any() else np.inf, 'wo_top5%': srt[k:].mean(),
         'Rpts': T.Rpts.median(), 'IS': T[T.yr <= 2024].pnl.mean(), 'OOS': T[T.yr == 2025].pnl.mean()}
    for y in (2023, 2024, 2025): r[y] = T[T.yr == y].pnl.mean()
    r['min_y'] = min(r[2023], r[2024], r[2025])
    return r
