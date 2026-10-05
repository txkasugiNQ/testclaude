import sys
sys.argv = ['x','2']
exec(open('battery.py').read().split('exits = [')[0])
pd.set_option('display.width',250)
rows=[]
for name in names:
    for ev in ['retest','reclaim','fade','closebrk']:
        for stopk in ([0,1.0] if ev=='reclaim' else [0.5,1.0]):
            sig = events(L[name], ev, stopk)
            for k in [1.5, 3]:
                s = sig.copy(); s['tp'] = s.eprice + s.side*k*(s.eprice-s.sl).abs()
                t = b.run(s, max_per_day=2); t = t[(t.split!='OOS')&(t.etod<=840)]
                for side in (1,-1):
                    r = dict(level=name, ev=ev, stop=stopk, k=k, side=side)
                    for sp in ('IS','VAL'):
                        q = t[(t.split==sp)&(t.side==side)]; r[f'n_{sp}']=len(q); r[f'e_{sp}']=q.R.mean() if len(q) else np.nan
                    rows.append(r)
D = pd.DataFrame(rows)
P = D.pivot_table(index=['level','ev','stop','k'], columns='side', values=['e_IS','e_VAL','n_IS'])
P.columns = [f'{a}_{"L" if b_>0 else "S"}' for a,b_ in P.columns]
P['min4'] = P[['e_IS_L','e_VAL_L','e_IS_S','e_VAL_S']].min(axis=1)
P = P[(P.n_IS_L>=50)&(P.n_IS_S>=50)]
print(P.sort_values('min4', ascending=False).head(25).round(3).to_string())
