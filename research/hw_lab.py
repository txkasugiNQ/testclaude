"""High-winrate / low-RR research lab.
Edge surface: for each event (entry on 1m bar, side, entry price, stop unit in points) compute the trade
result in R for every (stop multiple s, target rr*R, max-hold) cell, walking the 1m path forward.
Conservative intrabar rules (amb=0): adverse checked before favourable in every bar; gap through stop -> exit at open;
for LIMIT fills the fill bar only counts its CLOSE as favourable (high/low may precede the fill).
Optimistic sensitivity (amb=1): favourable checked first (upper bound, NOT used for decisions)."""
import numpy as np, pandas as pd
from numba import njit
from lab import B, daylevels
from levels import more_levels
from cand import daily_regime

@njit(cache=True)
def surface(o, h, l, c, tod, day, ent, side, epx, unit, limfill, rr, ss, holds, end_tod, amb):
    n = len(ent); S = len(ss); K = len(rr); H = len(holds); N = len(h)
    out = np.full((n, S, K, H), np.nan)
    for j in range(n):
        i0 = ent[j]; d = day[i0]; sd = side[j]; e = epx[j]; u = unit[j]
        for si in range(S):
            st = ss[si] * u
            for ki in range(K):
                tg = rr[ki] * st
                for hi in range(H):
                    mb = holds[hi]
                    res = np.nan
                    i = i0
                    while True:
                        first = (i == i0)
                        if sd > 0:
                            adv = e - l[i]; fav = (c[i] - e) if (first and limfill[j]) else (h[i] - e)
                            advo = e - o[i]
                        else:
                            adv = h[i] - e; fav = (e - c[i]) if (first and limfill[j]) else (e - l[i])
                            advo = o[i] - e
                        if (not first) and advo >= st:
                            res = -advo / st; break
                        hitS = adv >= st; hitT = fav >= tg
                        if hitS and hitT:
                            res = (rr[ki]) if amb == 1 else -1.0; break
                        if hitS: res = -1.0; break
                        if hitT: res = rr[ki]; break
                        if (i - i0 + 1) >= mb or tod[i] >= end_tod or i + 1 >= N or day[i + 1] != d:
                            res = (c[i] - e) * sd / st; break
                        i += 1
                    out[j, si, ki, hi] = res
    return out

class HW:
    def __init__(self, tf=2):
        self.b = B(tf); self.m = self.b.m; self.tf = tf
        self.L = more_levels(self.b)
        self.reg = np.nan_to_num(daily_regime(self.b, 50, 'ma'), nan=0)
        d = self.b.days; dv = d[d.rth_c.notna() & (d.n_pm >= 200)]
        self.adr = pd.Series(self.b.tdate).map((dv.rth_h - dv.rth_l).rolling(10, min_periods=5).mean().shift(1)).values
        self.year = pd.to_datetime(pd.Series(self.b.tdate)).dt.year.values
    # ---- entry helpers: signals are TF-bar indices known at TF close ----
    def market(self, sig, side):
        """market at the open of the next 1m bar after the TF close"""
        i1 = self.b.map1[sig] + 1
        ok = (i1 < len(self.m.o)) & (self.m.day[np.minimum(i1, len(self.m.o)-1)] == self.b.day[sig])
        sig, side, i1 = sig[ok], side[ok], i1[ok]
        return pd.DataFrame(dict(sig=sig, side=side, ent=i1, epx=self.m.o[i1], limfill=False))
    def limit(self, sig, side, price):
        """limit valid for the next TF bar; fills only if traded THROUGH by 1 tick; fill price = limit"""
        m = self.m; rows = []
        i1 = self.b.map1[sig] + 1
        for s, sd, p, a in zip(sig, side, price, i1):
            for i in range(a, min(a + self.tf, len(m.o))):
                if m.day[i] != self.b.day[s]: break
                if (sd > 0 and m.l[i] <= p - 0.25) or (sd < 0 and m.h[i] >= p + 0.25):
                    rows.append((s, sd, i, p, True)); break
        return pd.DataFrame(rows, columns=['sig','side','ent','epx','limfill'])
    def run(self, ev, unit_pts, rr, ss, holds, end_tod=960, amb=0, ent_lo=720, ent_hi=956):
        m = self.m
        et = m.tod[ev.ent.values]
        ok = (et - 1 >= ent_lo) & (et <= ent_hi) & np.isfinite(unit_pts) & (unit_pts > 0)
        ev = ev[ok].reset_index(drop=True); u = unit_pts[ok]
        R = surface(m.o, m.h, m.l, m.c, m.tod.astype(np.int64), m.day, ev.ent.values.astype(np.int64),
                    ev.side.values.astype(np.int64), ev.epx.values.astype(float), u.astype(float), ev.limfill.values.astype(np.bool_),
                    np.asarray(rr, float), np.asarray(ss, float), np.asarray(holds, np.int64), end_tod, amb)
        ev['split'] = m.split[ev.ent.values]; ev['year'] = pd.to_datetime(pd.Series(m.tdate[ev.ent.values])).dt.year.values
        ev['tdate'] = m.tdate[ev.ent.values]; ev['unit'] = u
        return ev, R

def first_per_day(ev, k=1):
    """keep the first k events per trading day (non-overlap proxy at screening stage)"""
    return ev.groupby('tdate', sort=False).head(k)

def summarize(ev, R, rr, ss, holds, splits=('IS','VAL'), min_n=40):
    rows = []
    for si, s in enumerate(ss):
        for ki, r in enumerate(rr):
            for hi, hd in enumerate(holds):
                x = R[:, si, ki, hi]
                row = dict(stop=s, tgt=r, hold=hd)
                for sp in splits:
                    msk = (ev.split.values == sp) & np.isfinite(x)
                    v = x[msk]
                    row[f'n_{sp}'] = len(v)
                    if len(v):
                        w = v > 0
                        row[f'exp_{sp}'] = v.mean(); row[f'wr_{sp}'] = w.mean()
                        row[f'aw_{sp}'] = v[w].mean() if w.any() else 0; row[f'al_{sp}'] = -v[~w].mean() if (~w).any() else 0
                rows.append(row)
    D = pd.DataFrame(rows)
    D['min_exp'] = D[[f'exp_{sp}' for sp in splits]].min(axis=1)
    D['min_wr'] = D[[f'wr_{sp}' for sp in splits]].min(axis=1)
    return D

@njit(cache=True)
def surface2(o, h, l, c, tod, day, ent, side, epx, tgt, stp, limfill, holds, end_tod):
    """per-event target and stop distances (points). returns R (in units of stop) per hold."""
    n = len(ent); H = len(holds); N = len(h)
    out = np.full((n, H), np.nan)
    for j in range(n):
        i0 = ent[j]; d = day[i0]; sd = side[j]; e = epx[j]; st = stp[j]; tg = tgt[j]
        for hi in range(H):
            mb = holds[hi]; i = i0; res = np.nan
            while True:
                first = (i == i0)
                if sd > 0:
                    adv = e - l[i]; fav = (c[i] - e) if (first and limfill[j]) else (h[i] - e); advo = e - o[i]
                else:
                    adv = h[i] - e; fav = (e - c[i]) if (first and limfill[j]) else (e - l[i]); advo = o[i] - e
                if (not first) and advo >= st: res = -advo / st; break
                if adv >= st: res = -1.0; break
                if fav >= tg: res = tg / st; break
                if (i - i0 + 1) >= mb or tod[i] >= end_tod or i + 1 >= N or day[i + 1] != d:
                    res = (c[i] - e) * sd / st; break
                i += 1
            out[j, hi] = res
    return out

def run2(H, ev, tgt_pts, stp_pts, holds, end_tod=960, ent_lo=720, ent_hi=956):
    m = H.m; et = m.tod[ev.ent.values]
    ok = (et - 1 >= ent_lo) & (et <= ent_hi) & np.isfinite(tgt_pts) & np.isfinite(stp_pts) & (tgt_pts > 0.5) & (stp_pts > 0)
    ev = ev[ok].reset_index(drop=True); tg = tgt_pts[ok]; st = stp_pts[ok]
    R = surface2(m.o, m.h, m.l, m.c, m.tod.astype(np.int64), m.day, ev.ent.values.astype(np.int64), ev.side.values.astype(np.int64),
                 ev.epx.values.astype(float), tg.astype(float), st.astype(float), ev.limfill.values.astype(np.bool_), np.asarray(holds, np.int64), end_tod)
    ev['split'] = m.split[ev.ent.values]; ev['year'] = pd.to_datetime(pd.Series(m.tdate[ev.ent.values])).dt.year.values
    ev['tdate'] = m.tdate[ev.ent.values]; ev['tgt'] = tg; ev['stp'] = st; ev['base'] = st / (st + tg)
    return ev, R
