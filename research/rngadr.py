exec(open('feat_brk.py').read().split("for exit_name, cfg in")[0])
for exit_name, cfg in [('TP3', dict(tp_R=3)), ('trail3/1.5', dict(tp_R=0, trail_start_R=3, trail_R=1.5))]:
    for regf in ['trend', 'none']:
        kw = {}
        if regf == 'none':
            kw['regime_fn'] = lambda m, reg: np.ones(len(reg))   # long allowed always...
        t_list = []
        if regf == 'none':
            tl = run(tf=2, entry_mode=1, wait_bars=1, s_stop=1.0, a_pull=0, allow_short=False, regime_fn=lambda m, r: np.ones(len(r)), **cfg)
            ts = run(tf=2, entry_mode=1, wait_bars=1, s_stop=1.0, a_pull=0, allow_long=False, regime_fn=lambda m, r: -np.ones(len(r)), **cfg)
            t = pd.concat([tl, ts])
        else:
            t = run(tf=2, entry_mode=1, wait_bars=1, s_stop=1.0, a_pull=0, **cfg)
        t = t[t.split!='OOS'].copy()
        t['rng_adr'] = F.rng_adr.values[t.sig.values]
        bins = [0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 10]
        q = pd.cut(t.rng_adr, bins)
        g = t.groupby([q,'split'], observed=True).R.agg(['mean','count']).unstack('split')
        print(f'=== {exit_name} regime={regf}')
        print(g.round(2).to_string())
