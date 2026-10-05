"""London opening-impulse continuation: at 08:00+X, if price moved >= thr*ATR from the 08:00 open, enter in that
direction at market; stop = s*ATR (or structural: beyond London extreme on the other side); exits: R targets, time exit, hold."""
import sys
from ldn_lab import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 2
R = LRun(tf); b = R.b; L = b.L
c, h, l, atr, day, t = b.c, b.h, b.l, b.atr, b.day, b.ltod
S = pd.Series
lon_hi = S(np.where(t > 480, h, -np.inf)).groupby(day).cummax().values
lon_lo = S(np.where(t > 480, l, np.inf)).groupby(day).cummin().values
op = L['lo_open']
def sigs(X, thr, stop='atr', s=1.5, splits=('IS', 'VAL')):
    i = np.where((t == 480 + X) & np.isin(b.split, splits) & np.isfinite(op))[0]
    mv = c[i] - op[i]; sel = np.abs(mv) >= thr * atr[i]; i, mv = i[sel], mv[sel]
    side = np.sign(mv).astype(int)
    sl = c[i] - side * s * atr[i] if stop == 'atr' else np.where(side > 0, lon_lo[i] - 0.25, lon_hi[i] + 0.25)
    d = pd.DataFrame(dict(sb=i, side=side, etype=0, eprice=c[i], sl=sl, expiry=1))
    r = (d.eprice - d.sl) * d.side
    return d[(r >= 2.0) & (r <= 8 * atr[i])]
def run(d, tp=None, max_bars=10**6, flat=720):
    d = d.copy()
    if tp is not None: d['tp'] = d.eprice + d.side * tp * (d.eprice - d.sl).abs()
    return R.run(d, max_per_day=1, max_bars=max_bars, flat=flat)
if __name__ == '__main__':
    print(f'##### tf={tf}  (stop 1.5 ATR unless noted)')
    for X in (6, 10, 16, 20, 30):
        if X % tf: continue
        for thr in (1, 2, 3, 4):
            d = sigs(X, thr)
            if len(d) < 40: continue
            o1 = summ(run(d, 1.0)); o2 = summ(run(d, 2.0)); o3 = summ(run(d, None, flat=540)); o4 = summ(run(d, 1.0, flat=540))
            print(f'X={X:2d}m thr>={thr} | TP1R {o1} | TP2R {o2} | exit 09:00 {o3} | TP1R or 09:00 {o4}')
    print('--- structural stop (beyond London extreme on the other side)')
    for X in (10, 16, 20):
        if X % tf: continue
        for thr in (2, 3):
            d = sigs(X, thr, stop='struct')
            print(f'X={X:2d}m thr>={thr} | TP1R {summ(run(d, 1.0))} | TP0.5R {summ(run(d, 0.5))} | exit 09:00 {summ(run(d, None, flat=540))}')
