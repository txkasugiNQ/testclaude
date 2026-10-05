import sys, time
from ldn_lab import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 2
R = LRun(tf); b = R.b; L = b.L
c, o, h, l, atr, day, t = b.c, b.o, b.h, b.l, b.atr, b.day, b.ltod
S = pd.Series
lag = lambda x, n: S(x).groupby(day).shift(n).values
lon = (t >= 480) & (t < 716) & (b.split != 'OOS')
def edge(cond):
    prev = S(cond).groupby(day).shift(1).fillna(False).values.astype(bool); return cond & ~prev
def mk(idx, side, etype, eprice, sl, tag):
    d = pd.DataFrame(dict(sb=idx, side=side, etype=etype, eprice=eprice, sl=sl, expiry=1))
    r = (d.eprice - d.sl) * d.side
    d = d[(r >= 0.5 * atr[idx]) & (r <= 6 * atr[idx]) & (r >= 2.0)]
    d['tag'] = tag; return d
ks = [0.33, 0.5, 1.0, 1.5, 2.0, 3.0, None]
rows = []
def evaluate(name, sig, mpd=2):
    if len(sig) < 60: return
    for k in ks:
        s = sig.copy()
        if k is not None:
            ref = s.eprice
            s['tp'] = ref + s.side * k * (ref - s.sl).abs()
        tt = R.run(s, max_per_day=mpd)
        for sp in ('IS', 'VAL'):
            q = tt[tt.split == sp]
            if len(q) == 0: continue
            rows.append(dict(strategy=name, tf=tf, tp='hold' if k is None else k, split=sp, n=len(q), tpd=len(q) / max(1, len(set(b.tdate[b.split == sp]))),
                             wr=(q.R > 0).mean(), exp=q.R.mean(), stop=q.risk.mean(), base=(1 / (1 + k)) if k else np.nan))
t0 = time.time()
# ---- 1/2: ORB continuation and ORB failure (fade) ----
for X in (15, 30, 60):
    H_, L_ = L[f'or{X}h'], L[f'or{X}l']; mid = (H_ + L_) / 2
    after = lon & (t >= 480 + X) & np.isfinite(H_)
    inside = after & (h < H_) & (l > L_)
    iu = np.where(inside)[0]
    for stopname, slu, sld in (('opp', L_ - 0.25, H_ + 0.25), ('mid', mid, mid)):
        sig = pd.concat([mk(iu, 1, 1, H_[iu] + 0.25, slu[iu], 'L'), mk(iu, -1, 1, L_[iu] - 0.25, sld[iu], 'S')])
        evaluate(f'ORB{X} break, stop={stopname}', sig, mpd=1)
    # failure: a bar broke above ORH and CLOSED back inside -> short at next open, stop above that bar's high
    fu = edge(after & (h > H_) & (c < H_) & (c > L_)); fd = edge(after & (l < L_) & (c > L_) & (c < H_))
    i1, i2 = np.where(fu)[0], np.where(fd)[0]
    sig = pd.concat([mk(i1, -1, 0, c[i1], h[i1] + 0.25, 'S'), mk(i2, 1, 0, c[i2], l[i2] - 0.25, 'L')])
    evaluate(f'ORB{X} failure fade', sig)
print('ORB', f'{time.time()-t0:.0f}s', flush=True)
# ---- 3/4/5: Asia, Frankfurt, prior-day ranges: break-continuation and sweep-reclaim fade ----
for nm, hk, lk in (('ASIA', 'asiah', 'asial'), ('FRA', 'frah', 'fral'), ('PD', 'pdh', 'pdl'), ('ON', 'onh', 'onl')):
    H_, L_ = L[hk], L[lk]; mid = (H_ + L_) / 2
    ok = lon & np.isfinite(H_) & np.isfinite(L_)
    iu = np.where(ok & (h < H_))[0]; idn = np.where(ok & (l > L_))[0]
    sig = pd.concat([mk(iu, 1, 1, H_[iu] + 0.25, H_[iu] + 0.25 - 1.0 * atr[iu], 'L'), mk(idn, -1, 1, L_[idn] - 0.25, L_[idn] - 0.25 + 1.0 * atr[idn], 'S')])
    evaluate(f'{nm} break (stop 1 ATR)', sig, mpd=1)
    fu = edge(ok & (h > H_) & (c < H_)); fd = edge(ok & (l < L_) & (c > L_))
    i1, i2 = np.where(fu)[0], np.where(fd)[0]
    sig = pd.concat([mk(i1, -1, 0, c[i1], h[i1] + 0.25, 'S'), mk(i2, 1, 0, c[i2], l[i2] - 0.25, 'L')])
    evaluate(f'{nm} sweep-reclaim fade', sig)
print('levels', f'{time.time()-t0:.0f}s', flush=True)
# ---- 6: fade / follow the first 30 or 60 minute move (one decision per day) ----
for X in (30, 60):
    at = lon & (t == 480 + X)
    i = np.where(at)[0]
    mv = c[i] - L['lo_open'][i]
    for thr in (0.0, 2.0):
        sel = np.abs(mv) >= thr * atr[i]
        ii, mvv = i[sel], mv[sel]
        ext_h = L[f'or{X}h'][np.minimum(ii + 1, len(c) - 1)]; ext_l = L[f'or{X}l'][np.minimum(ii + 1, len(c) - 1)]
        side = -np.sign(mvv).astype(int)
        sl = np.where(side < 0, ext_h + 0.25, ext_l - 0.25)
        evaluate(f'FADE first {X}m move (|move|>={thr}ATR)', mk(ii, side, 0, c[ii], sl, 'F'), mpd=1)
        side2 = -side
        sl2 = np.where(side2 > 0, c[ii] - 1.5 * atr[ii], c[ii] + 1.5 * atr[ii])
        evaluate(f'FOLLOW first {X}m move (|move|>={thr}ATR)', mk(ii, side2, 0, c[ii], sl2, 'M'), mpd=1)
print('first-move', f'{time.time()-t0:.0f}s', flush=True)
# ---- 7: simple mean reversion: price k ATR away from the 08:00 open -> fade ----
dist = (c - L['lo_open']) / atr
for kk in (3, 5, 8):
    cu = edge(lon & (dist >= kk)); cd = edge(lon & (dist <= -kk))
    i1, i2 = np.where(cu)[0], np.where(cd)[0]
    for s_ in (1.0, 2.0):
        sig = pd.concat([mk(i1, -1, 0, c[i1], c[i1] + s_ * atr[i1], 'S'), mk(i2, 1, 0, c[i2], c[i2] - s_ * atr[i2], 'L')])
        evaluate(f'MR {kk}ATR from London open, stop {s_}ATR', sig)
# ---- 8: compression box breakout ----
for N in (10, 20):
    bh = S(h).groupby(day).transform(lambda s: s.rolling(N, min_periods=N).max()).values
    bl = S(l).groupby(day).transform(lambda s: s.rolling(N, min_periods=N).min()).values
    tight = lon & ((bh - bl) <= 2.5 * atr)
    i = np.where(tight)[0]
    sig = pd.concat([mk(i, 1, 1, bh[i] + 0.25, bl[i] - 0.25, 'L'), mk(i, -1, 1, bl[i] - 0.25, bh[i] + 0.25, 'S')])
    evaluate(f'BOX{N} compression breakout (stop=box)', sig)
print('done', f'{time.time()-t0:.0f}s', flush=True)
D = pd.DataFrame(rows); D.to_pickle(f'ldn_simple_tf{tf}.pkl')
