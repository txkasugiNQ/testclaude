from ldn_lab import *
R = LRun(2); b = R.b
rng = np.random.default_rng(1)
idx = np.where((b.ltod >= 480) & (b.ltod < 700) & (b.split != 'OOS'))[0]
idx = np.sort(rng.choice(idx, 12000, replace=False)); side = rng.choice([-1, 1], len(idx))
for s_, k in ((1.0, 0.5), (1.0, 1.0), (1.5, 1.0), (1.0, 2.0)):
    st = s_ * b.atr[idx]
    sig = pd.DataFrame(dict(sb=idx, side=side, etype=0, sl=b.c[idx] - side * st, tp=b.c[idx] + side * k * st))
    t = R.run(sig)
    print(f'random market entries, stop {s_} ATR, TP {k}R: {summ(t)}   (random-walk WR {1/(1+k):.2f})')
print('mean 2m ATR in London (pts):', b.atr[(b.ltod > 480) & (b.ltod <= 720)].mean().round(2))
