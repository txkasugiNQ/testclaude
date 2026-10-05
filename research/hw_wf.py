exec(open('hw_vwb.py').read().split('# ---------- 1) MAE')[0])
import itertools
grid = list(itertools.product([2.4, 2.5, 2.6], [810, 840, 870], [0.5, 0.75, 1.0]))
cache = {}
for k, ws, tpk in grid:
    q = signals(k=k, stop='struct'); q['tp'] = q.eprice + q.side * tpk * (q.eprice - q.sl).abs()
    t = b.run(q, max_per_day=3, ent_start=ws, ent_end=956); t['q'] = pd.to_datetime(t.tdate).dt.to_period('Q')
    cache[(k, ws, tpk)] = t
W = []; log = []
for qq in pd.period_range('2023Q4', '2025Q4', freq='Q'):
    best = max(cache, key=lambda kk: cache[kk][cache[kk].q < qq].R.mean() if (cache[kk].q < qq).sum() >= 30 else -9)
    te = cache[best][cache[best].q == qq]; W.append(te)
    log.append(dict(q=str(qq), chosen=best, test_n=len(te), test_exp=te.R.mean() if len(te) else np.nan, test_wr=(te.R > 0).mean() if len(te) else np.nan))
W = pd.concat(W); print(pd.DataFrame(log).round(3).to_string())
for y in (2023, 2024, 2025):
    w = W[pd.to_datetime(W.tdate).dt.year == y]; print(f'WF {y}: n={len(w)} exp={w.R.mean():+.3f} wr={(w.R>0).mean():.2f}')
print(f'WF all: n={len(W)} exp={W.R.mean():+.3f} wr={(W.R>0).mean():.2f}')
pd.DataFrame(log).to_csv('../results/hw_walkforward_quarters.csv', index=False)
