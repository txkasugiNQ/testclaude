"""Single OOS evaluation + year-by-year + walk-forward-style yearly view + tail-risk, for pre-registered high-WR variants,
compared with the best high-RR candidates."""
exec(open('hw_vwb.py').read().split('# ---------- 1) MAE')[0])
import json
from smlab2 import run as smrun
def tail(r, label):
    r = np.asarray(r); n = len(r)
    w = r > 0; L_ = -r[~w]
    eq = np.cumsum(r); peak = np.maximum.accumulate(np.r_[0, eq])[1:]; dd = peak - eq
    # recovery: longest stretch (in trades) spent below a previous equity peak
    under = dd > 1e-9; longest = cur = 0
    for u in under:
        cur = cur + 1 if u else 0; longest = max(longest, cur)
    st = []; cur = 0
    for x in r:
        if x <= 0: cur += 1
        else:
            if cur: st.append(cur); cur = 0
    if cur: st.append(cur)
    srt = np.sort(r)
    ex = lambda k: srt[k:].mean() if n > k else np.nan        # drop k worst trades
    exw = lambda k: srt[:-k].mean() if n > k else np.nan      # drop k best trades
    tl = L_[L_ >= np.quantile(L_, 0.9)].sum() if len(L_) else 0
    return dict(strategy=label, trades=n, winrate=w.mean(), avg_win=r[w].mean(), avg_loss=L_.mean() if len(L_) else 0,
                expectancy=r.mean(), pf=r[w].sum()/L_.sum() if len(L_) else np.inf, max_dd=dd.max(), longest_underwater_trades=longest,
                max_losing_streak=max(st) if st else 0, avg_losing_streak=np.mean(st) if st else 0,
                largest_loss=-srt[0], loss_p95=np.quantile(L_, 0.95) if len(L_) else 0, loss_p99=np.quantile(L_, 0.99) if len(L_) else 0,
                exp_ex_worst1=ex(1), exp_ex_worst5=ex(5), exp_ex_worst10=ex(10), exp_ex_best5=exw(5), exp_ex_best10=exw(10),
                worst10pct_losses_share=tl / L_.sum() if len(L_) else 0)
P = json.load(open('PREREG_HW.json'))
res = {}
for vn, vv in P['variants'].items():
    q = signals(k=2.5, stop='struct'); q['tp'] = q.eprice + q.side * vv['tp_R'] * (q.eprice - q.sl).abs()
    t = b.run(q, max_per_day=3, ent_start=840, ent_end=956)
    t['year'] = pd.to_datetime(t.tdate).dt.year
    res[vn] = t
# comparison: high-RR candidates (state machine of record)
res['TDB (high-RR, pre-registered v1.0)'] = smrun(tf=2, entry_mode=1, wait_bars=1, a_pull=0, brk_end=840, ent_end=842, s_stop=1.25, td_min=0.4, tp_R=4)
res['TDC (3-yr selected, trail 2R/1R)'] = smrun(tf=3, entry_mode=2, wait_bars=1, a_pull=0, brk_end=840, ent_end=843, s_stop=1.5, td_min=0.5, tp_R=0, trail_start_R=2, trail_R=1)
pd.set_option('display.width', 250); pd.set_option('display.float_format', '{:.3f}'.format)
rows = []
for nm, t in res.items():
    t = t.copy(); t['year'] = pd.to_datetime(t.tdate).dt.year
    y = t.groupby('year').R.agg(['mean', 'count', lambda r: (r > 0).mean()])
    rows.append(dict(strategy=nm, **{f'exp_{yy}': y.loc[yy, 'mean'] for yy in y.index}, **{f'wr_{yy}': y.loc[yy, '<lambda_0>'] for yy in y.index},
                     **{f'n_{yy}': int(y.loc[yy, 'count']) for yy in y.index}, stop_pts=t.risk.mean()))
Y = pd.DataFrame(rows).set_index('strategy')
print('=== YEAR BY YEAR (2025 = holdout for VWR variants, evaluated once now)'); print(Y.round(3).to_string())
print('\n=== OOS 2025 ONLY, tail-risk view'); 
T25 = pd.DataFrame([tail(t[pd.to_datetime(t.tdate).dt.year == 2025].R.values, nm) for nm, t in res.items()]).set_index('strategy')
print(T25.T.round(3).to_string())
print('\n=== ALL 3 YEARS, tail-risk view')
TA = pd.DataFrame([tail(t.R.values, nm) for nm, t in res.items()]).set_index('strategy')
print(TA.T.round(3).to_string())
Y.to_csv('../results/hw_year_by_year.csv'); TA.to_csv('../results/hw_tailrisk_all_years.csv'); T25.to_csv('../results/hw_tailrisk_2025.csv')
for nm in ('VWR-0.5R', 'VWR-1R'): res[nm].to_csv(f'../results/hw_trades_{nm}.csv', index=False)
