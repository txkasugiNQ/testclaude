"""Phase 3 step 3: time-defined range -> breakout continuation.
Range = high/low of 1m bars with start time in [rs, re) (ET, same session). Breakout window: bars starting in [re, we).
Signal = FIRST 1m close beyond the range (above high -> long, below low -> short) inside the window (one per day per spec).
Entry = next bar open. Stops: 'opp' = other side of range, 'mid' = range midpoint, 'kDR' = signal close -/+ k*DR.
All stops are at least 0.03*DR from the signal close (avoid degenerate R), rounded to tick away from entry.
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from slots import ctx, run, TICK
from sim import params
def hm(s): a, b = s.split(':'); return int(a) * 60 + int(b)
_M = {}
def mats():
    if _M: return _M
    c = ctx(); df = c['df']
    g = df[df.good]
    gi = np.flatnonzero(df.good.values)
    piv = lambda col: g.pivot_table(index='sess', columns='smin', values=col).reindex(columns=range(1380))
    _M['C'] = piv('close'); _M['H'] = piv('high'); _M['L'] = piv('low')
    I = pd.Series(gi, index=pd.MultiIndex.from_arrays([g.sess.values, g.smin.values])).unstack().reindex(columns=range(1380))
    _M['I'] = I.reindex(_M['C'].index)
    _M['DR'] = g.groupby('sess').DR.first().reindex(_M['C'].index).values
    return _M
def sm(t): return (t - 1080) % 1440

def orb_entries(rs, re, we, stop='opp', k=0.1, min_dr=0.03, max_rng_dr=None, min_rng_dr=None):
    M = mats(); C, Hh, Ll, I, DR = M['C'].values, M['H'].values, M['L'].values, M['I'].values, M['DR']
    a, b, w = sm(hm(rs)), sm(hm(re)), sm(hm(we))
    hi = np.nanmax(Hh[:, a:b], axis=1); lo = np.nanmin(Ll[:, a:b], axis=1)
    win = C[:, b:w]
    up = win > hi[:, None]; dn = win < lo[:, None]
    brk = up | dn
    has = brk.any(1)
    j = np.argmax(brk, axis=1)
    rows = np.flatnonzero(has & np.isfinite(DR) & np.isfinite(hi))
    out = []
    for r in rows:
        jj = j[r]; col = b + jj
        d = 1 if up[r, jj] else -1
        sig = I[r, col]
        if not np.isfinite(sig) or col + 1 >= 1380 or not np.isfinite(I[r, col + 1]): continue
        rng = hi[r] - lo[r]
        if max_rng_dr is not None and rng > max_rng_dr * DR[r]: continue
        if min_rng_dr is not None and rng < min_rng_dr * DR[r]: continue
        cl = C[r, col]
        if stop == 'opp': st = lo[r] - TICK if d > 0 else hi[r] + TICK
        elif stop == 'mid': st = (hi[r] + lo[r]) / 2
        else: st = cl - d * k * DR[r]
        lim = cl - d * min_dr * DR[r]
        st = min(st, lim) if d > 0 else max(st, lim)
        st = np.floor(st / TICK) * TICK if d > 0 else np.ceil(st / TICK) * TICK
        out.append((int(sig) + 1, int(sig), d, st, DR[r], rng / DR[r]))
    E = pd.DataFrame(out, columns=['e', 'sig', 'd', 'stop', 'DR', 'rng_dr'])
    return E

SPECS = {  # name: (range start, range end, window end)
    'ORB5':  ('09:30', '09:35', '11:30'), 'ORB15': ('09:30', '09:45', '11:30'), 'ORB30': ('09:30', '10:00', '12:00'),
    'IB60':  ('09:30', '10:30', '13:00'), 'PRE':   ('08:00', '09:30', '11:00'), 'ONR':   ('18:00', '09:30', '12:00'),
    'ASIA':  ('18:00', '02:00', '06:00'), 'LDN':   ('02:00', '08:00', '11:00'), 'LUNCH': ('11:30', '13:00', '15:00'),
    'EARLYPM': ('12:00', '13:00', '15:00'),
}
if __name__ == '__main__':
    MG = {'t60': params(maxbars=60), 't120': params(maxbars=120), 'eod': params(maxbars=1000),
          'ATR8 eod': params(maxbars=1000, tr_type=2, tr_dist=8), 'ATR12 eod': params(maxbars=1000, tr_type=2, tr_dist=12),
          'R1@1 eod': params(maxbars=1000, tr_type=1, tr_dist=1.0, tr_act=1.0), 'swing30 eod': params(maxbars=1000, tr_type=4, tr_dist=30),
          'aggrBE.2': params(be_trig=0.2, be_off=0.05, tr_type=1, tr_act=0.3, tr_dist=0.25, maxbars=1000)}
    rows = []
    for nm, (rs, re, we) in SPECS.items():
        for stop, k in (('opp', 0), ('mid', 0), ('kDR', 0.1), ('kDR', 0.15)):
            E = orb_entries(rs, re, we, stop=stop, k=k)
            for mg, P in MG.items():
                Tt = run(E, P)
                r = {'spec': nm, 'stop': f'{stop}{k if k else ""}', 'mgmt': mg, 'n/day': len(Tt) / 730, 'exp': Tt.pnl.mean(),
                     'WR': (Tt.pnl > 1e-9).mean(), 'Rpts': Tt.Rpts.median()}
                for y in (2023, 2024, 2025): r[y] = Tt[Tt.yr == y].pnl.mean()
                rows.append(r)
        print(nm, flush=True)
    R = pd.DataFrame(rows); R['min_y'] = R[[2023, 2024, 2025]].min(axis=1)
    R.to_pickle('../output/p3_orb.pkl')
    pd.set_option('display.width', 250, 'display.max_rows', 400)
    print(R.sort_values('min_y', ascending=False).head(40).round(3).to_string(index=False))
    print(R[R.mgmt == 'eod'].round(3).to_string(index=False))
