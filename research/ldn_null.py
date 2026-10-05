from ldn_lab import *
m = LB(1)
df = pd.DataFrame(dict(day=m.day, t=m.ltod, o=m.o, h=m.h, l=m.l, c=m.c, sp=m.split))
lon = df[(df.t > 480) & (df.t <= 720) & (df.sp != 'OOS')]
rng = np.random.default_rng(0)
def stats_for(paths):
    """paths: list of (high_series_rel, low_series_rel) arrays relative to open"""
    th = []; tl = []; rev30 = []
    for H, Lw, C in paths:
        th.append(H.argmax()); tl.append(Lw.argmin())
        rev30.append((C[29], C[-1] - C[29]))
    th = np.array(th); tl = np.array(tl); r = np.array(rev30)
    return dict(h30=(th < 30).mean(), l30=(tl < 30).mean(), h60=(th < 60).mean(), l60=(tl < 60).mean(),
                corr30=np.corrcoef(r[:,0], r[:,1])[0,1])
real = []; days = []
for d, x in lon.groupby('day'):
    if len(x) != 240: continue
    o0 = x.o.iloc[0]
    real.append((x.h.values - o0, x.l.values - o0, x.c.values - o0)); days.append(x)
R = stats_for(real)
# null: shuffle 1m bars (as relative OHLC increments) within each 30-min bucket
null = []
for it in range(200):
    paths = []
    for x in days:
        o = x.o.values; h = x.h.values; l = x.l.values; c = x.c.values
        ret = c - o; up = h - o; dn = o - l                     # bar shape relative to its own open
        gap = o - np.r_[o[0], c[:-1]]                            # open vs previous close
        idx = np.arange(240)
        perm = np.concatenate([rng.permutation(idx[k:k+30]) for k in range(0, 240, 30)])
        ret, up, dn, gap = ret[perm], up[perm], dn[perm], gap[perm]
        cc = np.cumsum(gap + ret); oo = cc - ret
        paths.append((oo + up, oo - dn, cc))
    null.append(stats_for(paths))
N = pd.DataFrame(null)
print('statistic        real    null mean   null 2.5%-97.5%   real percentile')
for k in ('h30','l30','h60','l60','corr30'):
    print(f'{k:8s}  {R[k]:+.3f}   {N[k].mean():+.3f}     [{N[k].quantile(.025):+.3f}, {N[k].quantile(.975):+.3f}]    {(N[k] < R[k]).mean():.3f}')
