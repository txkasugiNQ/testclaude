exec(open('hw_vwb.py').read().split('# ---------- 1) MAE')[0])
print('band k | full PM 12:00-16:00 TP1R | late 14:00-16:00 TP1R | late TP0.75R  (IS/VAL exp, pooled n, WR)')
for k in (2.3, 2.4, 2.45, 2.5, 2.55, 2.6, 2.7):
    out = []
    for ws, tpk in ((720, 1.0), (840, 1.0), (840, 0.75)):
        q = signals(k=k, stop='struct'); q['tp'] = q.eprice + q.side * tpk * (q.eprice - q.sl).abs()
        t = b.run(q, max_per_day=3, ent_start=ws, ent_end=956); t = t[t.split != 'OOS']
        a = t[t.split == 'IS'].R.mean(); v = t[t.split == 'VAL'].R.mean()
        out.append(f'{a:+.2f}/{v:+.2f} ({len(t)},{(t.R>0).mean():.0%})')
    print(f'{k:5.2f} | ' + ' | '.join(out))
