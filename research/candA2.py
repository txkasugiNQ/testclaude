from cand import *
b = B(2)
S = pd.Series; L = daylevels(b)
reg = daily_regime(b, 50, 'ma')
ok = (b.tod >= 718) & (b.tod < 840) & np.isfinite(reg)
rows=[]
for side in (1,-1):
    X = L['rh'] if side>0 else L['rl']
    idx = np.where(ok)[0]; e = X[idx] + side*0.25
    rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=1, eprice=e, sl=e - side*b.atr[idx], expiry=1, reg=reg[idx])))
s = pd.concat(rows); s['tp'] = s.eprice + s.side*3*(s.eprice-s.sl).abs()
for side in (1,-1):
    for rg in (1,-1):
        t = b.run(s[(s.side==side)&(s.reg==rg)], max_per_day=2); t=t[t.split!='OOS']
        g = t.groupby('split').R.agg(['mean','count'])
        print(f'side {side:+d} regime {rg:+d}:', g.round(3).to_dict('index'))
