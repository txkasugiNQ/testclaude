import numpy as np, pandas as pd
from bars import build
from core import *
from engine import simulate

class B:
    def __init__(self, tf):
        x = build(tf)
        days = pd.read_pickle('days.pkl')
        good = days.index[(days.n_pm==240)]
        x = x[x.tdate.isin(set(good))].reset_index(drop=True)
        self.df = x; self.tf = tf
        self.o=x.o.values; self.h=x.h.values; self.l=x.l.values; self.c=x.c.values
        self.tod=x.tod.values.astype(np.int64); self.vw=x.vw.values; self.v=x.v.values.astype(float)
        self.tdate = x.tdate.values
        u, inv = np.unique(self.tdate, return_inverse=True)
        self.day = inv.astype(np.int64); self.udays = u
        self.split = split_of(self.tdate)
        # ATR(14) on this tf (true range)
        pc = np.r_[self.c[0], self.c[:-1]]
        tr = np.maximum(self.h-self.l, np.maximum(abs(self.h-pc), abs(self.l-pc)))
        self.atr = pd.Series(tr).ewm(alpha=1/14, adjust=False).mean().values
        self.days = days
        # 1-minute execution arrays
        if tf == 1:
            self.m = self
            self.map1 = np.arange(len(x))
        else:
            self.m = B(1)
            m = self.m
            key1 = pd.Series(np.arange(len(m.tod)), index=pd.MultiIndex.from_arrays([m.day, m.tod]))
            # map each TF bar to the last 1m bar with tod <= TF bar close (same day)
            k = m.day * 10000 + (m.tod + 2000)
            kt = self.day * 10000 + (self.tod + 2000)
            self.map1 = np.searchsorted(k, kt, side='right') - 1
            assert (m.day[self.map1] == self.day).all()
            # TF atr carried to 1m bars (value as of last completed TF bar)
            j = np.searchsorted(kt, k, side='right') - 1
            self.atr_on1 = np.where(j >= 0, self.atr[np.maximum(j,0)], np.nan)

    def run(self, sig, exec1=True, **kw):
        if exec1 and self.tf != 1:
            s = sig.copy(); s['sb_tf'] = s.sb; s['sb'] = self.map1[s.sb.values]
            m = self.m
            if 'expiry' in s: s['expiry'] = s.expiry * self.tf
            kw = dict(kw)
            if kw.get('max_bars', None) is not None and 'max_bars' in kw: kw['max_bars'] = kw['max_bars'] * self.tf
            if kw.get('trail_mode', 0) == 2: kw['trail_param'] = kw['trail_param'] * self.tf
            t = m._run(s, atr=self.atr_on1, **kw)
            t['tf'] = self.tf
            return t
        return self._run(sig, **kw)

    def _run(self, sig, atr=None, ent_start=720, ent_end=960, flat_tod=960, be_R=0., be_lock_R=0., trail_start_R=0., trail_mode=0,
            trail_param=0., part_R=0., part_frac=0., max_bars=10**6, max_per_day=99):
        s = sig.sort_values('sb', kind='stable').reset_index(drop=True)
        n=len(s)
        f = lambda k, d: s[k].values.astype(float) if k in s else np.full(n, d, float)
        out = simulate(self.o,self.h,self.l,self.c,self.tod,self.day,self.tf,
                       s.sb.values.astype(np.int64), s.side.values.astype(np.int64), s.etype.values.astype(np.int64),
                       f('eprice',np.nan), s.sl.values.astype(float), f('tp',np.nan), f('cancel',np.nan),
                       (s.expiry.values if 'expiry' in s else np.full(n,1)).astype(np.int64),
                       ent_start, ent_end, flat_tod, be_R, be_lock_R, trail_start_R, trail_mode, trail_param,
                       part_R, part_frac, max_bars, max_per_day, self.atr if atr is None else atr)
        cols = ['R','mfe','mae','eb','xb','epx','xpx','risk','reason']
        for cname, arr in zip(cols, out): s[cname] = arr
        t = s[s.eb >= 0].copy()
        t['tdate'] = self.tdate[t.eb.values]; t['split'] = self.split[t.eb.values]
        t['etod'] = self.tod[t.eb.values]; t['xtod'] = self.tod[t.xb.values]
        t['dur'] = (t.xb - t.eb + 1) * self.tf
        return t

def stats(t, ndays=None, cost_pts=0.0):
    if len(t)==0: return dict(n=0)
    r = t.R.values - cost_pts / t.risk.values
    w = r > 0
    gw = r[w].sum(); gl = -r[~w].sum()
    eq = np.cumsum(r); dd = (np.maximum.accumulate(np.r_[0,eq])[1:] - eq).max()
    # streaks
    streaks=[]; cur=0
    for x in r:
        if x <= 0: cur+=1
        else:
            if cur: streaks.append(cur); cur=0
    if cur: streaks.append(cur)
    nd = ndays if ndays else t.tdate.nunique()
    return dict(n=len(r), wr=w.mean(), avgW=r[w].mean() if w.any() else 0, avgL=-r[~w].mean() if (~w).any() else 0,
                exp=r.mean(), pf=gw/gl if gl>0 else np.inf, maxDD=dd, maxLS=max(streaks) if streaks else 0,
                avgLS=np.mean(streaks) if streaks else 0, tpd=len(r)/nd, risk=t.risk.mean(), dur=t.dur.mean(),
                totR=r.sum())

def report(t, b, label='', cost_pts=0.0, splits=('IS','VAL'), show=True):
    rows = {}
    for sp in splits:
        nd = (np.unique(b.tdate[b.split==sp])).size
        rows[sp] = stats(t[t.split==sp], nd, cost_pts)
    df = pd.DataFrame(rows).T
    if show:
        with pd.option_context('display.width',200, 'display.float_format', '{:.3f}'.format):
            print(label); print(df[['n','wr','avgW','avgL','exp','pf','maxDD','maxLS','tpd','risk','dur']])
    return df

def daylevels(b):
    """per-bar arrays of levels known at each bar close (no lookahead)."""
    df = b.df
    n = len(df); tod = b.tod
    g = df.groupby('tdate', sort=False)
    # running AM high/low (9:30-12:00), frozen after 12:00
    am = (tod > 570) & (tod <= 720)
    hh = np.where(am, b.h, -np.inf); ll = np.where(am, b.l, np.inf)
    amh = pd.Series(hh).groupby(b.day).cummax().values
    aml = pd.Series(ll).groupby(b.day).cummin().values
    on = (tod <= 570)
    onh = pd.Series(np.where(on, b.h, -np.inf)).groupby(b.day).cummax().values
    onl = pd.Series(np.where(on, b.l, np.inf)).groupby(b.day).cummin().values
    # running RTH high/low and PM high/low so far
    rth = tod > 570
    rh = pd.Series(np.where(rth, b.h, -np.inf)).groupby(b.day).cummax().values
    rl = pd.Series(np.where(rth, b.l, np.inf)).groupby(b.day).cummin().values
    pm = tod > 720
    ph = pd.Series(np.where(pm, b.h, -np.inf)).groupby(b.day).cummax().values
    pl = pd.Series(np.where(pm, b.l, np.inf)).groupby(b.day).cummin().values
    # rth open
    ro = pd.Series(np.where(tod == 570 + b.tf, b.o, np.nan)).groupby(b.day).transform('max').values
    # prior day RTH H/L/C
    d = b.days
    pdh = pd.Series(b.tdate).map(d.pdh).values; pdl = pd.Series(b.tdate).map(d.pdl).values; pdc = pd.Series(b.tdate).map(d.pdc).values
    return dict(amh=amh, aml=aml, onh=onh, onl=onl, rh=rh, rl=rl, ph=ph, pl=pl, ro=ro, pdh=pdh, pdl=pdl, pdc=pdc)

SHOW = ('IS','VAL')   # OOS masked during research
def ladder(b, sig, ks=(0.5,1,1.5,2,3,4), label='', **kw):
    """fixed TP at k*R for each k; prints expectancy per split"""
    rows=[]
    for k in ks:
        s = sig.copy()
        R = (s.eprice.fillna(0) - s.sl).abs() if 'eprice' in s else None
        s['tp'] = s.eprice + s.side * k * (s.eprice - s.sl).abs()
        t = b.run(s, **kw)
        for sp in SHOW:
            st = stats(t[t.split==sp]); st.update(k=k, sp=sp); rows.append(st)
    df = pd.DataFrame(rows)
    p = df.pivot(index='k', columns='sp', values='exp')[list(SHOW)]
    w = df.pivot(index='k', columns='sp', values='wr')[list(SHOW)]
    nn = df.pivot(index='k', columns='sp', values='n')[list(SHOW)]
    print(label, ' n=', nn.iloc[0].to_dict(), ' risk=%.1f' % df.risk.mean())
    with pd.option_context('display.float_format','{:.3f}'.format, 'display.width', 200):
        print(pd.concat([p.add_suffix('_exp'), w.add_suffix('_wr')], axis=1))
    return df

def quarters(t):
    """expectancy per calendar quarter (non-OOS only)"""
    q = pd.to_datetime(pd.Series(t.tdate.values)).dt.to_period('Q').astype(str).values
    tt = t.assign(q=q)
    tt = tt[tt.split!='OOS']
    return tt.groupby('q').R.agg(['mean','count'])
