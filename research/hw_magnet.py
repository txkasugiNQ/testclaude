from hw_lab import *
H = HW(2); b = H.b; L = H.L
c, h, l, atr, day, tod = b.c, b.h, b.l, b.atr, b.day, b.tod
S = pd.Series
lag = lambda x, n: S(x).groupby(day).shift(n).values
win = (tod >= 718) & (tod < 956) & (b.split != 'OOS')
def edge(cond):
    prev = S(cond).groupby(day).shift(1).fillna(False).values.astype(bool); return cond & ~prev
holds = [10, 30, 10000]
rows = []
L['r100'] = np.round(c / 100) * 100
def report(name, ev, R):
    for hi, hd in enumerate(holds):
        x = R[:, hi]
        for sp in ('IS', 'VAL'):
            msk = (ev.split.values == sp) & np.isfinite(x)
            v = x[msk]
            if len(v) < 30: continue
            rows.append(dict(test=name, hold=hd, split=sp, n=len(v), wr=(v > 0).mean(), base=ev.base.values[msk].mean(),
                             avg_tgt_R=(ev.tgt.values/ev.stp.values)[msk].mean(), exp=v.mean(), stop_pts=ev.stp.values[msk].mean()))
# ---- A) MAGNET: price within d ATR of an untouched-for-N-bars level -> trade TOWARD it, target = touch
for lv in ('vw', 'pdc', 'ro', 'p12', 'r100', 'poc', 'mid'):
    X = L[lv]
    touched = (l <= X) & (h >= X)
    recent = S(touched.astype(float)).groupby(day).transform(lambda s: s.rolling(10, min_periods=1).max()).values > 0
    for d in (0.5, 1.0, 2.0):
        for s_ in (1.0, 2.0):
            dist = (X - c)
            cond = edge(win & np.isfinite(X) & ~recent & (np.abs(dist) <= d * atr) & (np.abs(dist) >= 0.25 * atr))
            idx = np.where(cond)[0]
            side = np.sign(dist[idx]).astype(int)
            ev = H.market(idx, side)
            X_ = X[ev.sig.values]
            tg = (X_ - ev.epx.values) * ev.side.values + 0.25
            st = s_ * atr[ev.sig.values]
            ev, R = run2(H, ev, tg, st, holds)
            report(f'MAGNET {lv} d<={d} stop{s_}', ev, R)
# ---- B) RETEST: price broke a level by >= d ATR (first time) -> trade BACK to the level, target = touch
for up, dn in (('amh','aml'), ('ibh','ibl'), ('onh','onl'), ('pdh','pdl'), ('vwu2','vwd2'), ('rh_prev','rl_prev')):
    if up == 'rh_prev':
        Xu = lag(L['rh'], 20); Xd = lag(L['rl'], 20)    # session extreme from 40 min earlier
    else:
        Xu, Xd = L[up], L[dn]
    for d in (0.5, 1.0, 2.0):
        for s_ in (1.0, 2.0):
            cu = edge(win & ((c - Xu) >= d * atr)); cd = edge(win & ((Xd - c) >= d * atr))
            sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[-np.ones(cu.sum(), int), np.ones(cd.sum(), int)]
            o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_])
            X_ = np.where(ev.side.values < 0, Xu[ev.sig.values], Xd[ev.sig.values])
            tg = (X_ - ev.epx.values) * ev.side.values + 0.25
            st = s_ * atr[ev.sig.values]
            ev, R = run2(H, ev, tg, st, holds)
            report(f'RETEST {up}/{dn} d>={d} stop{s_}', ev, R)
# ---- C) VWAP-band MR with level exits (target = VWAP, 1sd band, 1.5sd band)
vw, vsd = L['vw'], L['vsd']
for k in (2.0, 2.5, 3.0):
    tu = edge(win & (h >= vw + k * vsd)) & (c < vw + k * vsd); td_ = edge(win & (l <= vw - k * vsd)) & (c > vw - k * vsd)
    sig = np.r_[np.where(tu)[0], np.where(td_)[0]]; side = np.r_[-np.ones(tu.sum(), int), np.ones(td_.sum(), int)]
    o_ = np.argsort(sig); ev0 = H.market(sig[o_], side[o_])
    ext = np.where(ev0.side.values < 0, h[ev0.sig.values], l[ev0.sig.values])
    for stopmode in ('struct', 'atr1.5'):
        st = (np.abs(ext - ev0.epx.values) + 0.25) if stopmode == 'struct' else 1.5 * atr[ev0.sig.values]
        st = np.where(st >= 0.5 * atr[ev0.sig.values], st, np.nan)
        for tname, tk in (('VWAP', 0.0), ('1sd', 1.0), ('1.5sd', 1.5), ('2sd', 2.0)):
            if tk >= k: continue
            X_ = vw[ev0.sig.values] - ev0.side.values * tk * vsd[ev0.sig.values]
            tg = (X_ - ev0.epx.values) * ev0.side.values
            ev, R = run2(H, ev0.copy(), tg, st, holds)
            report(f'VWB {k}sd reject -> {tname} stop={stopmode}', ev, R)
D = pd.DataFrame(rows)
P = D.pivot_table(index=['test','hold'], columns='split', values=['n','wr','base','avg_tgt_R','exp','stop_pts'])
P.columns = [f'{a}_{b_}' for a, b_ in P.columns]
P['edge_IS'] = P.wr_IS - P.base_IS; P['edge_VAL'] = P.wr_VAL - P.base_VAL
P['min_exp'] = P[['exp_IS','exp_VAL']].min(axis=1)
P = P.reset_index(); P.to_pickle('hw_magnet.pkl')
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 300)
cols = ['test','hold','n_IS','n_VAL','avg_tgt_R_IS','base_IS','wr_IS','wr_VAL','edge_IS','edge_VAL','exp_IS','exp_VAL','stop_pts_IS']
print('== top by min(IS,VAL) expectancy'); print(P.sort_values('min_exp', ascending=False).head(20)[cols].round(3).to_string())
print('== top by min edge over baseline (WR - random-walk WR)'); P['min_edge'] = P[['edge_IS','edge_VAL']].min(axis=1)
print(P.sort_values('min_edge', ascending=False).head(15)[cols].round(3).to_string())
print('cells', len(P), ' with min_exp>=0.35:', (P.min_exp>=0.35).sum(), '>=0.25:', (P.min_exp>=0.25).sum(), '>=0.15:', (P.min_exp>=0.15).sum())
