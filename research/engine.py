"""First-passage / excursion engine (conservative, no look-ahead).

Entry: at OPEN of bar e (= signal bar + 1). Direction d=+1 long / -1 short.
Stop fixed at `stop` for this analysis (management is studied later).
Per forward bar j (j=0 is the entry bar itself): fav_j, adv_j in R from bar high/low.
A target a is 'hit' at the first bar where fav >= a; stop at first bar where adv >= 1.
If both on the same bar -> counted as STOP FIRST (conservative).
Path stops at session end (no overnight holding).
"""
import numpy as np

TARGETS = np.array([0.15, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0])

def excursions(df_arrays, e, d, entry, R, H=60, with_close=False):
    hi, lo, sess = df_arrays['high'], df_arrays['low'], df_arrays['sess']
    n = len(hi)
    idx = e[:, None] + np.arange(H)[None, :]
    valid = idx < n
    idx = np.minimum(idx, n - 1)
    valid &= sess[idx] == sess[e][:, None]
    h, l = hi[idx], lo[idx]
    fav = np.where(d[:, None] > 0, h - entry[:, None], entry[:, None] - l) / R[:, None]
    adv = np.where(d[:, None] > 0, entry[:, None] - l, h - entry[:, None]) / R[:, None]
    fav[~valid] = -np.inf; adv[~valid] = -np.inf
    if with_close:
        cl = (df_arrays['close'][idx] - entry[:, None]) * d[:, None] / R[:, None]
        op = (df_arrays['open'][idx] - entry[:, None]) * d[:, None] / R[:, None]   # open of each bar in R (gap fills)
        return fav, adv, valid, (cl, op)
    return fav, adv, valid

def first_idx(mask):
    """first True index along axis 1, H if none"""
    H = mask.shape[1]
    any_ = mask.any(1)
    return np.where(any_, mask.argmax(1), H)

def outcomes(fav, adv, valid, cl=None):
    H = fav.shape[1]
    t_stop = first_idx(adv >= 1.0)
    out = {'t_stop': t_stop}
    for a in TARGETS:
        t_a = first_idx(fav >= a)
        out[f't_{a}'] = t_a
        out[f'win_{a}'] = t_a < t_stop                     # strictly earlier bar (tie -> stop)
    # MFE before stop (bars strictly before the stop bar; on stop bar, intrabar order unknown -> ignore its high)
    j = np.arange(H)[None, :]
    pre = j < t_stop[:, None]
    out['mfe_pre_stop'] = np.where(pre, fav, -np.inf).max(1).clip(min=0)
    # MFE/MAE over fixed horizons (incl. beyond stop - pure path information)
    for h in (10, 30, 60):
        m = valid[:, :h]
        out[f'mfe{h}'] = np.where(m, fav[:, :h], -np.inf).max(1)
        out[f'mae{h}'] = np.where(m, adv[:, :h], -np.inf).max(1)
    # MAE before reaching +1R (for trades that get there, bars up to and incl. hit bar)
    t1 = out['t_1.0']
    m = j <= t1[:, None]
    out['mae_pre_1R'] = np.where(m & valid, adv, -np.inf).max(1)
    t05 = out['t_0.5']
    m = j <= t05[:, None]
    out['mae_pre_05R'] = np.where(m & valid, adv, -np.inf).max(1)
    out['n_valid'] = valid.sum(1)
    if cl is not None:
        cl, op = cl
        rows = np.arange(len(cl))
        # stop fill: at stop, or at the bar open if that bar opened beyond the stop (gap) -> worse fill
        stop_fill = -np.maximum(1.0, -op[rows, np.minimum(t_stop, H - 1)])
        out['stop_fill'] = stop_fill
        last = valid.sum(1) - 1                          # last valid bar (time / session-end exit, MTM at its close)
        mtm = cl[np.arange(len(cl)), np.maximum(last, 0)]
        for a in (0.5, 1.0, 2.0):
            ta = out[f't_{a}']
            out[f'ev_{a}'] = np.where(ta < t_stop, a, np.where(t_stop < H, stop_fill, np.minimum(mtm, a)))
            # note: ta==t_stop (same bar) -> stop (conservative); unresolved -> MTM
            out[f'ev_{a}'] = np.where((t_stop < H) & (t_stop <= ta), stop_fill, out[f'ev_{a}'])
    return out
