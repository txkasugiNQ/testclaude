import itertools
exec(open('ldn_validate.py').read().split("from hw_validate_tail import tail")[0])
def lom_g(X, thr, s, tp):
    i = np.where((t == 480 + X) & np.isfinite(op))[0]
    mv = c[i] - op[i]; sel = np.abs(mv) >= thr * atr[i]; i, mv = i[sel], mv[sel]; side = np.sign(mv).astype(int)
    d = pd.DataFrame(dict(sb=i, side=side, etype=0, eprice=c[i], sl=c[i] - side * s * atr[i], expiry=1))
    d['tp'] = d.eprice + d.side * tp * (d.eprice - d.sl).abs(); return R.run(d, max_per_day=1)
def ler_g(T, thr):
    i = np.where((t == T) & np.isfinite(op))[0]
    mv = c[i] - op[i]; sel = np.abs(mv) >= thr * atr[i]; i, mv = i[sel], mv[sel]; side = -np.sign(mv).astype(int)
    sl = np.where(side < 0, lon_hi[i] + 0.25, lon_lo[i] - 0.25)
    d = pd.DataFrame(dict(sb=i, side=side, etype=0, eprice=c[i], sl=sl, expiry=1, tp=op[i]))
    r = (d.eprice - d.sl) * d.side; d = d[(r >= 2.0) & (r <= 6 * atr[i]) & ((d.tp - d.eprice) * d.side > 0.5)]
    return R.run(d, max_per_day=1)
fams = {'LOM': {k: lom_g(*k) for k in itertools.product([10, 16], [1, 2, 3], [1.0, 1.5], [0.5, 1.0, 1.5])},
        'LER': {k: ler_g(*k) for k in itertools.product([540, 570, 600], [2, 3, 4])}}
for fam, cache in fams.items():
    for tt in cache.values(): tt['q'] = pd.to_datetime(tt.tdate).dt.to_period('Q')
    W = []; log = []
    for qq in pd.period_range('2023Q4', '2025Q4', freq='Q'):
        best = max(cache, key=lambda k: cache[k][cache[k].q < qq].R.mean() if (cache[k].q < qq).sum() >= 40 else -9)
        te = cache[best][cache[best].q == qq]; W.append(te)
        log.append(f'{qq}:{best}->{te.R.mean():+.2f}({len(te)})')
    W = pd.concat(W)
    print(f'=== {fam} walk-forward: ' + ' | '.join(log))
    for y in (2023, 2024, 2025):
        w = W[W.year == y]; print(f'   WF {y}: n={len(w)} exp={w.R.mean():+.3f} wr={(w.R>0).mean():.2f}')
    print(f'   WF all: n={len(W)} exp={W.R.mean():+.3f} wr={(W.R>0).mean():.2f}')
