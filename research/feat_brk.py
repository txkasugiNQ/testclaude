from smlab2 import *
m = M()
S = pd.Series
day = m.day; tod = m.tod; c = m.c
days = m.days
# 1m-based features known at the 1m bar index (signal bar close)
vw = m.vw
vwlag = S(vw).groupby(day).shift(30).values
F = pd.DataFrame(index=np.arange(len(c)))
F['vw_slope30'] = (vw - vwlag)
ro = S(m.tdate).map(days.rth_open).values; pdc = S(m.tdate).map(days.pdc).values
F['am_ret'] = c - ro
F['vs_pdc'] = c - pdc
F['dist_vw'] = c - vw
rng_so_far = S(np.where(tod>570, m.h, -np.inf)).groupby(day).cummax().values - S(np.where(tod>570, m.l, np.inf)).groupby(day).cummin().values
adr = S(m.tdate).map((days.rth_h - days.rth_l).where(days.n_pm>=200).shift(1).rolling(10, min_periods=5).mean()).values
F['rng_adr'] = rng_so_far / adr
F['tod'] = tod
v = S(m.v); F['rvol10'] = (v.groupby(day).transform(lambda s: s.rolling(10, min_periods=1).sum()) / v.groupby(tod).transform(lambda s: s.shift(1).rolling(20, min_periods=5).mean()*10)).values
F['onr'] = S(m.tdate).map(days.onh - days.onl).values / adr
F['dow'] = pd.to_datetime(S(m.tdate)).dt.dayofweek.values
for exit_name, cfg in [('TP3', dict(tp_R=3)), ('trail3/1.5', dict(tp_R=0, trail_start_R=3, trail_R=1.5))]:
    t = run(tf=2, entry_mode=1, wait_bars=1, s_stop=1.0, a_pull=0, **cfg)
    t = t[t.split!='OOS'].copy()
    X = F.loc[t.sig.values].reset_index(drop=True)
    t = t.reset_index(drop=True).join(X)
    for f in ['vw_slope30','am_ret','vs_pdc','dist_vw','rng_adr','tod','rvol10','onr']:
        x = t[f] * (t.side if f in ('vw_slope30','am_ret','vs_pdc','dist_vw') else 1)
        q = pd.qcut(x.rank(method='first'), 3, labels=['lo','mid','hi'])
        g = t.groupby([q, 'split']).R.mean().unstack()
        n = t.groupby([q, 'split']).R.size().unstack()
        print(exit_name, f'{f:12s}', ' | '.join(f'{k}: IS {g.loc[k,"IS"]:+.2f}({n.loc[k,"IS"]}) VAL {g.loc[k,"VAL"]:+.2f}({n.loc[k,"VAL"]})' for k in ['lo','mid','hi']))
    g = t.groupby(['dow','split']).R.mean().unstack(); print(exit_name, 'dow', g.round(2).to_dict())
