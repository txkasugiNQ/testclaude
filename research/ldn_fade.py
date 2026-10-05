"""Fade the early-London move. One decision per day at time T: if price moved >= thr from the 08:00 open,
enter against it at market (next 1m open); stop beyond the 08:00..T extreme on the move's side; flat 12:00."""
import sys
from ldn_lab import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 2
R = LRun(tf); b = R.b; L = b.L
c, h, l, atr, day, t = b.c, b.h, b.l, b.atr, b.day, b.ltod
S = pd.Series
lon_hi = S(np.where(t > 480, h, -np.inf)).groupby(day).cummax().values
lon_lo = S(np.where(t > 480, l, np.inf)).groupby(day).cummin().values
op = L['lo_open']; adr = L['adr']
def sigs(T, thr, unit='atr', stopbuf=0.25):
    i = np.where((t == T) & (b.split != 'OOS') & np.isfinite(op))[0]
    mv = c[i] - op[i]
    scale = atr[i] if unit == 'atr' else adr[i]
    sel = np.abs(mv) >= thr * scale
    i, mv = i[sel], mv[sel]
    side = -np.sign(mv).astype(int)
    sl = np.where(side < 0, lon_hi[i] + stopbuf, lon_lo[i] - stopbuf)
    d = pd.DataFrame(dict(sb=i, side=side, etype=0, eprice=c[i], sl=sl, expiry=1, op=op[i]))
    r = (d.eprice - d.sl) * d.side
    return d[(r >= 2.0) & (r <= 6 * atr[i])]
def run(d, tp):
    d = d.copy()
    if tp == 'open': d['tp'] = d.op
    elif tp == 'half': d['tp'] = (d.op + d.eprice) / 2
    elif tp == 'hold': pass
    else: d['tp'] = d.eprice + d.side * tp * (d.eprice - d.sl).abs()
    return R.run(d, max_per_day=1)
print(f'=== tf={tf}: decision time x move threshold (ATR), target = hold to 12:00 | TP 2R | TP back to 08:00 open')
for T in (510, 525, 540, 555, 570, 600):
    for thr in (0, 1, 2, 3):
        d = sigs(T, thr)
        out = [summ(run(d, tp)) for tp in ('hold', 2.0, 'open')]
        print(f'{T//60:02d}:{T%60:02d} thr>={thr}ATR | hold {out[0]} | TP2R {out[1]} | to-open {out[2]}')
