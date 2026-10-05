from ldn_lab import *
import json, importlib.util
P = json.load(open('PREREG_LDN.json'))
R = LRun(2); b = R.b; L = b.L
c, h, l, atr, day, t = b.c, b.h, b.l, b.atr, b.day, b.ltod
S = pd.Series
lon_hi = S(np.where(t > 480, h, -np.inf)).groupby(day).cummax().values
lon_lo = S(np.where(t > 480, l, np.inf)).groupby(day).cummin().values
op = L['lo_open']
ALL = ('IS', 'VAL', 'OOS')
def lom(tp):
    i = np.where((t == 496) & np.isfinite(op))[0]
    mv = c[i] - op[i]; sel = np.abs(mv) >= 2.0 * atr[i]; i, mv = i[sel], mv[sel]
    side = np.sign(mv).astype(int)
    d = pd.DataFrame(dict(sb=i, side=side, etype=0, eprice=c[i], sl=c[i] - side * 1.5 * atr[i], expiry=1))
    d['tp'] = d.eprice + d.side * tp * (d.eprice - d.sl).abs()
    return R.run(d, max_per_day=1)
def ler():
    i = np.where((t == 570) & np.isfinite(op))[0]
    mv = c[i] - op[i]; sel = np.abs(mv) >= 3.0 * atr[i]; i, mv = i[sel], mv[sel]
    side = -np.sign(mv).astype(int)
    sl = np.where(side < 0, lon_hi[i] + 0.25, lon_lo[i] - 0.25)
    d = pd.DataFrame(dict(sb=i, side=side, etype=0, eprice=c[i], sl=sl, expiry=1, tp=op[i]))
    r = (d.eprice - d.sl) * d.side
    d = d[(r >= 2.0) & (r <= 6 * atr[i]) & ((d.tp - d.eprice) * d.side > 0.5)]
    return R.run(d, max_per_day=1)
from hw_validate_tail import tail
res = {f'LOM TP{k}R': lom(k) for k in P['LOM']['variants_tp_R']}
res['LER to-open'] = ler()
pd.set_option('display.width', 250); pd.set_option('display.float_format', '{:.3f}'.format)
rows = []
for nm, tt in res.items():
    r = dict(strategy=nm)
    for sp in ALL:
        q = tt[tt.split == sp]; r[f'exp_{sp}'] = q.R.mean(); r[f'wr_{sp}'] = (q.R > 0).mean(); r[f'n_{sp}'] = len(q); r[f'stop_{sp}'] = q.risk.mean()
    for y in (2023, 2024, 2025):
        q = tt[tt.year == y]; r[f'exp_{y}'] = q.R.mean()
    rows.append(r)
Y = pd.DataFrame(rows).set_index('strategy')
print('=== PRE-REGISTERED LONDON CANDIDATES (2025 = untouched holdout, evaluated once)')
print(Y[['n_IS','n_VAL','n_OOS','exp_IS','exp_VAL','exp_OOS','wr_IS','wr_VAL','wr_OOS','stop_IS','stop_OOS','exp_2023','exp_2024','exp_2025']].round(3).to_string())
print('\n=== tail / risk view, OOS 2025')
print(pd.DataFrame([tail(tt[tt.split == 'OOS'].R.values, nm) for nm, tt in res.items()]).set_index('strategy').T.round(3).to_string())
Y.to_csv('../results/ldn_prereg_results.csv')
for nm, tt in res.items(): tt.to_csv(f'../results/ldn_trades_{nm.replace(" ", "_")}.csv', index=False)
