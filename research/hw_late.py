exec(open('hw_vwb.py').read().split('# ---------- 1) MAE')[0])
rows = []
for k in (2.0, 2.25, 2.5, 2.75):
    for ws in (780, 810, 840, 870):
        for tpk in (0.5, 0.75, 1.0, 1.25):
            q = signals(k=k, stop='struct'); q['tp'] = q.eprice + q.side * tpk * (q.eprice - q.sl).abs()
            t = b.run(q, max_per_day=3, ent_start=ws, ent_end=956)
            r = dict(k=k, start=ws, tp=tpk)
            for sp in ('IS', 'VAL'):
                x = t[t.split == sp]; r[f'n_{sp}'] = len(x); r[f'e_{sp}'] = x.R.mean(); r[f'wr_{sp}'] = (x.R > 0).mean()
            x = t[t.split != 'OOS']; r['e_pool'] = x.R.mean(); r['wr_pool'] = (x.R > 0).mean(); r['n_pool'] = len(x)
            rows.append(r)
D = pd.DataFrame(rows); D['min'] = D[['e_IS', 'e_VAL']].min(axis=1)
pd.set_option('display.width', 220); pd.set_option('display.max_rows', 100)
for tpk in (0.5, 0.75, 1.0, 1.25):
    q = D[D.tp == tpk].assign(cell=lambda x: x.e_IS.round(2).astype(str) + '/' + x.e_VAL.round(2).astype(str) + ' (' + x.n_pool.astype(str) + ',' + (x.wr_pool*100).round(0).astype(int).astype(str) + '%)')
    print(f'--- TP {tpk}R : IS/VAL expectancy (pooled n, pooled WR); rows=band, cols=window start')
    print(q.pivot(index='k', columns='start', values='cell').to_string())
D.to_pickle('hw_late.pkl')
