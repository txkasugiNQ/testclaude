import sys, time
sys.argv = ['x','2']
exec(open('battery.py').read().split('exits = [')[0])
# extra levels
raw = pd.read_pickle('bars2.pkl')
raw = raw[raw.tdate.isin(set(b.udays))].reset_index(drop=True)
assert len(raw)==len(b.c)
d = b.days.copy()
d = d[d.rth_c.notna() & (d.n_pm>=200)]
dt = pd.to_datetime(pd.Series(d.index))
wk = dt.dt.to_period('W').values
dd = pd.DataFrame(dict(h=d.rth_h.values, l=d.rth_l.values, wk=wk), index=d.index)
wh = dd.groupby('wk').h.max(); wl = dd.groupby('wk').l.min()
prev_wh = wh.shift(1); prev_wl = wl.shift(1)
L['pwh'] = pd.Series(b.tdate).map(pd.Series(prev_wh.reindex(dd.wk).values, index=dd.index)).values
L['pwl'] = pd.Series(b.tdate).map(pd.Series(prev_wl.reindex(dd.wk).values, index=dd.index)).values
L['pdpmh'] = pd.Series(b.tdate).map(d.pmh.shift(1)).values
L['pdpml'] = pd.Series(b.tdate).map(d.pml.shift(1)).values
# ETH vwap: need 2m bar last value of vwap_eth -> rebuild from 1m
m1 = pd.read_pickle('nq2.pkl')
m1['tod2'] = m1.tod.where(m1.tod <= 1020, m1.tod - 1440)
m1['b'] = ((m1.tod2 - 1)//2 + 1)*2
ve = m1.groupby(['tdate','b']).vwap_eth.last()
key = pd.MultiIndex.from_arrays([b.tdate, b.tod])
L['vwe'] = ve.reindex(key).values
names = ['vwe','pwh','pwl','pdpmh','pdpml']
exits = [('R1.5',dict(k=1.5)),('R2',dict(k=2)),('R3',dict(k=3)),('trail',dict(trail_mode=1, trail_start_R=1.5, trail_param=1.0))]
rows=[]
for name in names:
    for ev in ['brk','fade','reclaim','closebrk']:
        for stopk in ([0, 1.0] if ev=='reclaim' else [0.5, 1.0, 1.5]):
            sig = events(L[name], ev, stopk)
            if len(sig) < 50: continue
            for xn, xp in exits:
                s = sig.copy()
                kw = {k:v for k,v in xp.items() if k!='k'}
                if 'k' in xp: s['tp'] = s.eprice + s.side*xp['k']*(s.eprice - s.sl).abs()
                t = b.run(s, max_per_day=2, **kw); t = t[t.split!='OOS']
                for ws, we in [(720,960),(720,840),(810,960)]:
                    tt = t[(t.etod - 1 >= ws) & (t.etod <= we)]
                    for side in (1,-1):
                        r = dict(level=name, ev=ev, stop=stopk, exit=xn, win=f'{ws}-{we}', side=side)
                        for sp in ('IS','VAL'):
                            q = tt[(tt.split==sp)&(tt.side==side)]
                            r[f'n_{sp}'] = len(q); r[f'exp_{sp}'] = q.R.mean() if len(q) else np.nan
                        rows.append(r)
    print(name, len(rows), flush=True)
R = pd.DataFrame(rows); R['min'] = R[['exp_IS','exp_VAL']].min(axis=1)
R = R[(R.n_IS>=60)&(R.n_VAL>=20)]
pd.set_option('display.width',200)
print(R.sort_values('min', ascending=False).head(25).round(3).to_string())
