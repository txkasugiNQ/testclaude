import numpy as np
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
