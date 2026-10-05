import sys
from ldn_lab import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 2
R = LRun(tf); b = R.b; L = b.L
c, o, h, l, atr, day, t = b.c, b.o, b.h, b.l, b.atr, b.day, b.ltod
S = pd.Series
lon = (t >= 480) & (t < 716) & (b.split != 'OOS')
def edge(cond):
    prev = S(cond).groupby(day).shift(1).fillna(False).values.astype(bool); return cond & ~prev
def mk(idx, side, sl, tp=None, etype=0, eprice=None):
    d = pd.DataFrame(dict(sb=idx, side=side, etype=etype, eprice=c[idx] if eprice is None else eprice, sl=sl, expiry=1))
    if tp is not None: d['tp'] = tp
    r = (d.eprice - d.sl) * d.side
    ok = (r >= 0.5 * atr[idx]) & (r <= 6 * atr[idx]) & (r >= 2.0)
    if tp is not None: ok &= ((d.tp - d.eprice) * d.side > 0.5)
    return d[ok]
def show(name, d, mpd=1, ks=(None, 0.5, 1.0, 2.0)):
    out = []
    for k in ks:
        q = d.copy()
        if k is not None: q['tp'] = q.eprice + q.side * k * (q.eprice - q.sl).abs()
        out.append(('own' if k is None else f'{k}R') + ' ' + summ(R.run(q, max_per_day=mpd)))
    print(f'{name:55s} | ' + ' || '.join(out))
print(f'##### tf={tf}')
# A) range return after sweep-reclaim of Asia / overnight range: target = mid / far side
for nm, hk, lk in (('ASIA', 'asiah', 'asial'), ('ON', 'onh', 'onl')):
    H_, L_ = L[hk], L[lk]; mid = (H_ + L_) / 2
    ok = lon & np.isfinite(H_)
    i1 = np.where(edge(ok & (h > H_) & (c < H_)))[0]; i2 = np.where(edge(ok & (l < L_) & (c > L_)))[0]
    for tname, tu, td in (('mid', mid, mid), ('far side', L_, H_)):
        d = pd.concat([mk(i1, -1, h[i1] + 0.25, tu[i1]), mk(i2, 1, l[i2] - 0.25, td[i2])])
        show(f'{nm} sweep-reclaim -> {tname}', d, mpd=2, ks=(None,))
# B) Frankfurt hand-off: at 08:00 close, fade/follow the 07:00-08:00 move
i = np.where(lon & (t == 480 + tf))[0]
fra_mv = L['lo_open'][i] - S(np.where(t == 420 + tf, o, np.nan)).groupby(day).transform('max').values[i]
for thr in (0, 2):
    sel = np.abs(fra_mv) >= thr * atr[i]; ii = i[sel]; sgn = np.sign(fra_mv[sel]).astype(int)
    show(f'FADE Frankfurt-hour move at 08:0x (>= {thr}ATR), stop 1.5ATR', mk(ii, -sgn, c[ii] + sgn * 1.5 * atr[ii]), ks=(0.5, 1.0, 2.0, None))
    show(f'FOLLOW Frankfurt-hour move at 08:0x (>= {thr}ATR), stop 1.5ATR', mk(ii, sgn, c[ii] - sgn * 1.5 * atr[ii]), ks=(0.5, 1.0, 2.0, None))
# C) first 5/10/15 minutes impulse: fade / follow
for X in (6, 10, 16):
    if X % tf: continue
    i = np.where(lon & (t == 480 + X))[0]
    mv = c[i] - L['lo_open'][i]
    hh = S(np.where(t > 480, h, -np.inf)).groupby(day).cummax().values[i]; ll = S(np.where(t > 480, l, np.inf)).groupby(day).cummin().values[i]
    for thr in (1, 3):
        sel = np.abs(mv) >= thr * atr[i]; ii = i[sel]; sgn = np.sign(mv[sel]).astype(int)
        slf = np.where(sgn > 0, hh[sel] + 0.25, ll[sel] - 0.25)
        show(f'FADE first {X}m impulse (>= {thr}ATR), stop beyond extreme', mk(ii, -sgn, slf), ks=(0.5, 1.0, 2.0, None))
        show(f'FOLLOW first {X}m impulse (>= {thr}ATR), stop 1.5ATR', mk(ii, sgn, c[ii] - sgn * 1.5 * atr[ii]), ks=(0.5, 1.0, 2.0, None))
# D) magnets: Globex open / prior RTH close, first time price is 2-6 ATR away in London -> trade toward it, target = touch
for nm in ('gx_open', 'pdc'):
    X_ = L[nm]; dist = (X_ - c) / atr
    cond = edge(lon & np.isfinite(X_) & (np.abs(dist) >= 2) & (np.abs(dist) <= 6))
    ii = np.where(cond)[0]; sgn = np.sign(dist[ii]).astype(int)
    for s_ in (1.5, 3.0):
        show(f'MAGNET {nm} (2-6 ATR away) target=touch, stop {s_}ATR', mk(ii, sgn, c[ii] - sgn * s_ * atr[ii], X_[ii]), ks=(None,))
# E) breakout with close confirmation (market entry) instead of stop orders, Asia/ON levels
for nm, hk, lk in (('ASIA', 'asiah', 'asial'), ('ON', 'onh', 'onl')):
    H_, L_ = L[hk], L[lk]; ok = lon & np.isfinite(H_)
    pc = S(c).groupby(day).shift(1).values
    i1 = np.where(ok & (c > H_) & (pc <= H_))[0]; i2 = np.where(ok & (c < L_) & (pc >= L_))[0]
    d = pd.concat([mk(i1, 1, c[i1] - 1.5 * atr[i1]), mk(i2, -1, c[i2] + 1.5 * atr[i2])])
    show(f'{nm} close-break continuation (market), stop 1.5ATR', d, ks=(0.5, 1.0, 2.0, None))
