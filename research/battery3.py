import sys, time
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
RANDOM = len(sys.argv)>2 and sys.argv[2]=='random'
sys.argv = ['x', str(tf)]
exec(open('battery.py').read().split('exits = [')[0])
from cand import daily_regime
yr = pd.to_datetime(pd.Series(b.tdate)).dt.year.values
reg = np.nan_to_num(daily_regime(b, 50, 'ma'), nan=0)
d = b.days; dv = d[d.rth_c.notna() & (d.n_pm>=200)]
adr = pd.Series(b.tdate).map((dv.rth_h-dv.rth_l).rolling(10, min_periods=5).mean().shift(1)).values
ro = L['ro']
rng = np.random.default_rng(1)
exits = [('R1',dict(k=1)),('R1.5',dict(k=1.5)),('R2',dict(k=2)),('R3',dict(k=3)),('trail',dict(trail_mode=1, trail_start_R=1.5, trail_param=1.0))]
rows=[]; t0=time.time()
for name in names:
    for ev in ['brk','fade','reclaim','closebrk']:
        for stopk in ([0, 1.0] if ev=='reclaim' else [0.75, 1.25]):
            sig0 = events(L[name], ev, stopk)
            if len(sig0) < 50: continue
            if RANDOM:   # destroy direction information: random side, mirror stop
                flip = rng.choice([-1,1], len(sig0))
                sig0 = sig0.copy(); sig0['side'] = sig0.side*flip
                sig0['sl'] = sig0.eprice - (sig0.eprice - sig0.sl)*flip
                sig0.loc[sig0.etype==1, 'etype'] = 0; sig0.loc[sig0.etype==2,'etype']=0   # market entries to avoid invalid stop/limit geometry
            for filt in ['none','trend','trendday']:
                sig = sig0
                if filt == 'trend':
                    sig = sig0[reg[sig0.sb.values] == sig0.side.values]
                elif filt == 'trendday':
                    i_ = sig0.sb.values
                    sig = sig0[(reg[i_] == sig0.side.values) & ((b.c[i_] - ro[i_])*sig0.side.values >= 0.3*adr[i_])]
                if len(sig) < 40: continue
                for xn, xp in exits:
                    s = sig.copy()
                    kw = {k:v for k,v in xp.items() if k!='k'}
                    if 'k' in xp: s['tp'] = s.eprice + s.side*xp['k']*(s.eprice - s.sl).abs()
                    t = b.run(s, max_per_day=2, **kw)
                    t['yr'] = yr[t.eb.values] if False else pd.to_datetime(t.tdate).dt.year.values
                    for ws, we in [(720,960),(720,840),(810,960)]:
                        tt = t[(t.etod - 1 >= ws) & (t.etod <= we)]
                        r = dict(level=name, ev=ev, stop=stopk, filt=filt, exit=xn, win=f'{ws}-{we}')
                        for y in (2023, 2024, 2025):
                            q = tt[tt.yr==y]; r[f'n{y}'] = len(q); r[f'e{y}'] = q.R.mean() if len(q) else np.nan
                        rows.append(r)
    print(name, len(rows), f'{time.time()-t0:.0f}s', flush=True)
R = pd.DataFrame(rows)
R['min'] = R[['e2023','e2024','e2025']].min(axis=1)
R['nmin'] = R[['n2023','n2024','n2025']].min(axis=1)
R.to_pickle(f'battery3_tf{tf}{"_random" if RANDOM else ""}.pkl')
ok = R[R.nmin>=40]
print('configs', len(ok), ' pass(min>=0.35):', (ok['min']>=0.35).sum(), ' pass(min>=0.25):', (ok['min']>=0.25).sum(), ' pass(min>=0.15):', (ok['min']>=0.15).sum())
pd.set_option('display.width',220)
print(ok.sort_values('min', ascending=False).head(25).round(3).to_string())
