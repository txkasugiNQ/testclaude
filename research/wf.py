from validate import *
import itertools
m = M()
grid = list(itertools.product([0.3, 0.4, 0.5], [1.0, 1.25, 1.5], [('TP3',dict(tp_R=3)),('TP4',dict(tp_R=4)),('tr3/1.5',dict(tp_R=0,trail_start_R=3,trail_R=1.5))]))
# precompute trades for every grid point over full data
cache = {}
for td, st, (xn, xc) in grid:
    t = final_trades(td_min=td, s_stop=st, **xc)
    t['q'] = pd.to_datetime(t.tdate).dt.to_period('Q')
    cache[(td, st, xn)] = t
quarters = pd.period_range('2023Q4', '2025Q4', freq='Q')
wf_trades = []; log=[]
for q in quarters:
    best=None; bscore=-9
    for k, t in cache.items():
        tr = t[t.q < q]
        if len(tr) < 40: continue
        sc = tr.R.mean()
        if sc > bscore: bscore, best = sc, k
    te = cache[best]; te = te[te.q == q]
    wf_trades.append(te.assign(wf_q=str(q), chosen=str(best)))
    log.append(dict(q=str(q), chosen=best, train_exp=round(bscore,3), test_n=len(te), test_exp=round(te.R.mean(),3) if len(te) else np.nan))
W = pd.concat(wf_trades)
print(pd.DataFrame(log).to_string())
print('WF all test quarters:', f'n={len(W)} exp={W.R.mean():+.3f} wr={(W.R>0).mean():.2f}')
for y in ['2023','2024','2025']:
    w = W[W.wf_q.str.startswith(y)]
    print(' WF', y, f'n={len(w)} exp={w.R.mean():+.3f} wr={(w.R>0).mean():.2f}')
W.to_pickle('wf_trades.pkl')
