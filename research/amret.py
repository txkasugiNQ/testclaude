exec(open('feat_brk.py').read().split("for exit_name, cfg in")[0])
F['amr_adr'] = F.am_ret / adr
for tf in (2,3):
  for exit_name, cfg in [('TP3', dict(tp_R=3)), ('tr3/1.5', dict(tp_R=0, trail_start_R=3, trail_R=1.5)), ('hold', dict(tp_R=0))]:
    t = run(tf=tf, entry_mode=1, wait_bars=1, s_stop=1.0, a_pull=0, **cfg)
    t = t[t.split!='OOS'].copy()
    t['x'] = F.amr_adr.values[t.sig.values] * t.side
    bins = [-10, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 10]
    g = t.groupby([pd.cut(t.x, bins), 'split'], observed=True).R.agg(['mean','count']).unstack('split')
    print(f'=== tf{tf} {exit_name}  (x = signed (price - RTH open)/ADR at signal)')
    print(g.round(2).to_string())
    for thr in [0.1, 0.2, 0.3]:
        q = t[t.x >= thr]
        print(f'   x>={thr}: ' + ' '.join(f'{sp}:{q[q.split==sp].R.mean():+.3f}(n={len(q[q.split==sp])},wr={(q[q.split==sp].R>0).mean():.2f})' for sp in ['IS','VAL']))
