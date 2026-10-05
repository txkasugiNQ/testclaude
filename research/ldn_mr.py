"""Event-based London mean reversion to the 08:00 open: first time (after start) price is >= k*ATR from the
London open -> fade at market; stop beyond running London extreme; target = 08:00 open (or alternatives); flat 12:00."""
import sys
from ldn_lab import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 2
R = LRun(tf); b = R.b; L = b.L
c, h, l, atr, day, t = b.c, b.h, b.l, b.atr, b.day, b.ltod
S = pd.Series
lon_hi = S(np.where(t > 480, h, -np.inf)).groupby(day).cummax().values
lon_lo = S(np.where(t > 480, l, np.inf)).groupby(day).cummin().values
op = L['lo_open']
def edge(cond):
    prev = S(cond).groupby(day).shift(1).fillna(False).values.astype(bool); return cond & ~prev
def sigs(start, k, end=660, splits=('IS','VAL')):
    win = (t >= start) & (t <= end) & np.isin(b.split, splits) & np.isfinite(op)
    dist = (c - op) / atr
    cu = edge(win & (dist >= k)); cd = edge(win & (dist <= -k))
    i1, i2 = np.where(cu)[0], np.where(cd)[0]
    d = pd.concat([pd.DataFrame(dict(sb=i1, side=-1, sl=lon_hi[i1] + 0.25)), pd.DataFrame(dict(sb=i2, side=1, sl=lon_lo[i2] - 0.25))])
    d['etype'] = 0; d['eprice'] = c[d.sb.values]; d['expiry'] = 1; d['op'] = op[d.sb.values]
    r = (d.eprice - d.sl) * d.side
    return d[(r >= 2.0) & (r <= 6 * atr[d.sb.values])].sort_values('sb')
def run(d, tp):
    d = d.copy()
    if tp == 'open': d['tp'] = d.op
    elif tp == 'half': d['tp'] = (d.op + d.eprice) / 2
    elif tp != 'hold': d['tp'] = d.eprice + d.side * tp * (d.eprice - d.sl).abs()
    return R.run(d, max_per_day=1)
if __name__ == '__main__':
    print(f'=== tf={tf} event-based fade toward London open (first trigger per day)')
    for start in (510, 540, 570, 600):
        for k in (2, 3, 4, 5):
            d = sigs(start, k)
            out = [summ(run(d, tp)) for tp in ('open', 'half', 1.0, 'hold')]
            print(f'start {start//60:02d}:{start%60:02d} k>={k}ATR | to-open {out[0]} | half-way {out[1]} | 1R {out[2]} | hold {out[3]}')
