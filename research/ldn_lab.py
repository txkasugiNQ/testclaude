"""London-session lab. Times are London clock minutes of bar CLOSE relative to London midnight of the trading date (ltod)."""
import numpy as np, pandas as pd
from core import split_of
LO, LE = 480, 720          # London session 08:00-12:00
class LB:
    def __init__(self, tf):
        x = pd.read_pickle(f'lbars{tf}.pkl')
        days = pd.read_pickle('days.pkl')
        # keep trading days that have a complete 07:00-12:00 London window
        cnt = x[(x.ltod > 420) & (x.ltod <= 720)].groupby('tdate').size()
        good = set(cnt.index[cnt >= 0.95 * (300 // tf)])
        x = x[x.tdate.isin(good)].reset_index(drop=True)
        self.df = x; self.tf = tf
        self.o, self.h, self.l, self.c = x.o.values, x.h.values, x.l.values, x.c.values
        self.v = x.v.values.astype(float); self.ltod = x.ltod.values.astype(np.int64); self.tod = x.tod.values.astype(np.int64)
        self.tdate = x.tdate.values
        u, inv = np.unique(self.tdate, return_inverse=True); self.day = inv.astype(np.int64); self.udays = u
        self.split = split_of(self.tdate)
        pc = np.r_[self.c[0], self.c[:-1]]
        tr = np.maximum(self.h - self.l, np.maximum(abs(self.h - pc), abs(self.l - pc)))
        self.atr = pd.Series(tr).ewm(alpha=1/14, adjust=False).mean().values
        self.days = days
        self._levels()
    def _levels(self):
        S = pd.Series; day = self.day; t = self.ltod
        def run_hi(mask): return S(np.where(mask, self.h, -np.inf)).groupby(day).cummax().values
        def run_lo(mask): return S(np.where(mask, self.l, np.inf)).groupby(day).cummin().values
        def frozen(arr, until):   # value as of time 'until', broadcast to bars after it (nan before)
            v = S(np.where(t <= until, arr, np.nan)).groupby(day).transform('last').values
            return np.where(t > until, v, np.nan)
        on = t <= 420                                   # Globex open -> 07:00 London
        asia = (t > 0) & (t <= 420)                     # 00:00-07:00 London
        fra = (t > 420) & (t <= 480)                    # Frankfurt hour 07:00-08:00
        pre = t <= 480                                  # everything before London open
        L = {}
        L['onh'] = frozen(run_hi(pre), 480); L['onl'] = frozen(run_lo(pre), 480)
        L['asiah'] = frozen(run_hi(asia), 420); L['asial'] = frozen(run_lo(asia), 420)
        L['frah'] = frozen(run_hi(fra), 480); L['fral'] = frozen(run_lo(fra), 480)
        L['lo_open'] = S(np.where(t == 480 + self.tf, self.o, np.nan)).groupby(day).transform('max').values   # 08:00 open
        for m in (15, 30, 60):
            orb = (t > 480) & (t <= 480 + m)
            L[f'or{m}h'] = frozen(run_hi(orb), 480 + m); L[f'or{m}l'] = frozen(run_lo(orb), 480 + m)
        lon = t > 480
        L['ldh'] = run_hi(lon); L['ldl'] = run_lo(lon)      # running London-session high/low (incl. current bar)
        d = self.days; td = S(self.tdate)
        L['pdh'] = td.map(d.pdh).values; L['pdl'] = td.map(d.pdl).values; L['pdc'] = td.map(d.pdc).values
        L['gx_open'] = S(self.o).groupby(day).transform('first').values        # 18:00 ET Globex open
        dv = d[d.rth_c.notna() & (d.n_pm >= 200)]
        L['adr'] = td.map((dv.rth_h - dv.rth_l).rolling(10, min_periods=5).mean().shift(1)).values
        self.L = L

from engine import simulate
class LRun:
    """signals on TF bars (London lab), execution on 1m bars, engine = conservative simulator (ltod used as clock)."""
    def __init__(self, tf):
        self.b = LB(tf); self.m = LB(1) if tf != 1 else self.b; self.tf = tf
        b, m = self.b, self.m
        dm = {d: i for i, d in enumerate(m.udays)}
        bday_in_m = np.array([dm.get(d, -1) for d in b.tdate])
        k1 = m.day * 100000 + (m.ltod + 3000); kt = bday_in_m * 100000 + (b.ltod + 3000)
        self.map1 = np.searchsorted(k1, kt, side='right') - 1
        self.valid = (bday_in_m >= 0) & (self.map1 >= 0)
        self.valid[self.valid] &= (m.day[self.map1[self.valid]] == bday_in_m[self.valid])
        j = np.searchsorted(kt, k1, side='right') - 1
        self.atr_on1 = np.where(j >= 0, b.atr[np.maximum(j, 0)], np.nan) if tf != 1 else b.atr
    def run(self, sig, ent_start=480, ent_end=716, flat=720, max_per_day=99, be_R=0., be_lock_R=0., trail_start_R=0., trail_mode=0,
            trail_param=0., part_R=0., part_frac=0., max_bars=10**6):
        s = sig[self.valid[sig.sb.values]].copy() if self.tf != 1 else sig.copy()
        s['sb_tf'] = s.sb.values; s['sb'] = self.map1[s.sb.values] if self.tf != 1 else s.sb.values
        s = s.sort_values('sb', kind='stable').reset_index(drop=True)
        n = len(s); m = self.m
        f = lambda k, d: s[k].values.astype(float) if k in s else np.full(n, d, float)
        exp = (s.expiry.values if 'expiry' in s else np.ones(n)).astype(np.int64) * self.tf
        if trail_mode == 2: trail_param = trail_param * self.tf
        out = simulate(m.o, m.h, m.l, m.c, m.ltod, m.day, 1, s.sb.values.astype(np.int64), s.side.values.astype(np.int64),
                       s.etype.values.astype(np.int64), f('eprice', np.nan), s.sl.values.astype(float), f('tp', np.nan), f('cancel', np.nan),
                       exp, ent_start, ent_end, flat, be_R, be_lock_R, trail_start_R, trail_mode, trail_param, part_R, part_frac,
                       max_bars * self.tf, max_per_day, self.atr_on1)
        for cname, arr in zip(['R','mfe','mae','eb','xb','epx','xpx','risk','reason'], out): s[cname] = arr
        t = s[s.eb >= 0].copy()
        t['tdate'] = m.tdate[t.eb.values]; t['split'] = m.split[t.eb.values]; t['etod'] = m.ltod[t.eb.values]
        t['year'] = pd.to_datetime(pd.Series(t.tdate.values)).dt.year.values; t['dur'] = t.xb - t.eb + 1
        return t
def summ(t, splits=('IS', 'VAL')):
    out = []
    for sp in splits:
        q = t[t.split == sp]
        if len(q) == 0: out.append(f'{sp}: n=0'); continue
        out.append(f'{sp}:{q.R.mean():+.3f}(n={len(q)},wr={(q.R>0).mean():.2f},stop={q.risk.mean():.1f})')
    return ' '.join(out)
