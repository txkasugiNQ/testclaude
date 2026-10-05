import sys
sys.argv=['x','2']
exec(open('battery.py').read().split('exits = [')[0])
d = b.days.copy()
d['rth_c'] = d['rth_c']
for w in [10, 20, 50]:
    d[f'ma{w}'] = d.rth_c.rolling(w).mean()   # includes day itself -> shift for use
    d[f'reg{w}'] = np.sign(d.rth_c.shift(1) - d[f'ma{w}'].shift(1))  # known before the session
pd.set_option('display.width',250)
for lev_up, lev_dn in [('rh_prev','rl_prev'),('amh','aml'),('luh','lul'),('vwu2','vwd2')]:
  for ev in ['brk','closebrk']:
    for stopk in [1.0, 1.5]:
        su = events(L[lev_up], ev, stopk); su = su[su.side>0]
        sd = events(L[lev_dn], ev, stopk); sd = sd[sd.side<0]
        sig = pd.concat([su, sd])
        for w in [20, 50]:
            reg = pd.Series(b.tdate[sig.sb.values]).map(d[f'reg{w}']).values
            s = sig[reg == sig.side.values]
            for k in [2, 3]:
                s2 = s.copy(); s2['tp'] = s2.eprice + s2.side*k*(s2.eprice-s2.sl).abs()
                t = b.run(s2, max_per_day=2); t = t[(t.split!='OOS')&(t.etod<=840)]
                g = t.groupby(['split','side']).R.agg(['mean','count']).unstack('side')
                print(f'{lev_up}/{lev_dn} {ev} stop{stopk} MA{w} R{k}:', ' '.join(f'{sp}:L={g.loc[sp,("mean",1)]:+.2f}({int(g.loc[sp,("count",1)])}) S={g.loc[sp,("mean",-1)]:+.2f}({int(g.loc[sp,("count",-1)])})' for sp in ['IS','VAL'] if sp in g.index))
