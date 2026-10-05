"""Deep dive: VWAP 2.5-sigma band rejection fade (best mean-reversion family), realistic non-overlapping trades."""
from hw_lab import *
from path import path_stats
from lab import stats
H = HW(2); b = H.b; L = H.L; m = H.m
c, o, h, l, atr, day, tod = b.c, b.o, b.h, b.l, b.atr, b.day, b.tod
S = pd.Series
win = (tod >= 718) & (tod < 956)
def edge(cond):
    prev = S(cond).groupby(day).shift(1).fillna(False).values.astype(bool); return cond & ~prev
vw, vsd = L['vw'], L['vsd']
def signals(k=2.5, stop='struct', s_atr=1.0, tp=None, tp_level=None):
    up, dn = vw + k*vsd, vw - k*vsd
    tu = edge(win & (h >= up)) & (c < up); td_ = edge(win & (l <= dn)) & (c > dn)
    rows = []
    for cond, sd in ((tu, -1), (td_, 1)):
        idx = np.where(cond)[0]
        e = c[idx]          # reference (fill is next open)
        if stop == 'struct': sl = np.where(sd < 0, h[idx] + 0.25, l[idx] - 0.25)
        else: sl = e - sd * s_atr * atr[idx]
        d = pd.DataFrame(dict(sb=idx, side=sd, etype=0, eprice=e, sl=sl, expiry=1))
        if tp_level is not None:
            d['tp'] = vw[idx] - sd * tp_level * vsd[idx]
        rows.append(d)
    s = pd.concat(rows).sort_values('sb')
    R0 = (s.eprice - s.sl).abs(); s = s[(R0 >= 0.5*atr[s.sb.values]) & (R0 <= 4*atr[s.sb.values])]
    return s
def line(t, label):
    out = []
    for sp in ('IS', 'VAL'):
        q = t[t.split == sp]
        if len(q) == 0: continue
        st = stats(q)
        out.append(f"{sp}: n={st['n']} WR={st['wr']:.2f} avgW={st['avgW']:.2f} avgL={st['avgL']:.2f} exp={st['exp']:+.3f} PF={st['pf']:.2f} maxLS={st['maxLS']} stop={st['risk']:.1f}")
    print(f'{label:45s} ' + ' | '.join(out))
# ---------- 1) MAE analysis: how far do eventual winners go against? ----------
s = signals(stop='atr', s_atr=1.0)
ev = H.market(s.sb.values, s.side.values)
ev = ev[(m.split[ev.ent.values] != 'OOS')]
unit = b.atr[ev.sig.values]
ks = np.array([0.25, 0.5, 1.0, 1.5, 2.0])
mb, tr, mfe, mae, fin = path_stats(m.h, m.l, m.c, m.tod, m.day, ev.ent.values.astype(np.int64), ev.side.values.astype(np.int64), ev.epx.values, unit, ks, 960)
print('=== MAE (in ATR, ATR~%.1f pts) BEFORE reaching +k ATR, VWB 2.5sd rejection, IS+VAL' % unit.mean())
for j, k in enumerate(ks):
    r = ~np.isnan(mb[:, j]); x = mb[r, j]
    print(f'  +{k} ATR reached {r.mean():.2f} | MAE before: p50={np.median(x):.2f} p75={np.quantile(x,.75):.2f} p90={np.quantile(x,.9):.2f} p95={np.quantile(x,.95):.2f} ATR')
# structural distance (bar extreme to entry) for reference
s2 = signals(stop='struct'); print('  structural stop (rejection-bar extreme) mean %.1f pts = %.2f ATR' % ((s2.eprice - s2.sl).abs().mean(), ((s2.eprice - s2.sl).abs()/atr[s2.sb.values]).mean()))
# ---------- 2) exit comparison (non-overlapping, max 3/day) ----------
print('\n=== EXIT COMPARISON (structural stop beyond rejection-bar extreme)')
base = signals(stop='struct')
for k_ in (0.25, 0.33, 0.5, 0.67, 0.75, 1.0, 1.5):
    q = base.copy(); q['tp'] = q.eprice + q.side * k_ * (q.eprice - q.sl).abs()
    line(b.run(q, max_per_day=3), f'fixed TP {k_}R')
for lvl, nm in ((1.5, '1.5sd band'), (1.0, '1sd band'), (0.0, 'VWAP')):
    q = signals(stop='struct', tp_level=lvl); line(b.run(q, max_per_day=3), f'MR exit at {nm}')
q = base.copy()
line(b.run(q, max_per_day=3, part_R=0.5, part_frac=0.5, be_R=-1), 'partial 50%@0.5R + BE runner (to 16:00)')
q2 = signals(stop='struct', tp_level=0.0)
line(b.run(q2, max_per_day=3, part_R=0.5, part_frac=0.5, be_R=-1), 'partial 50%@0.5R + BE runner to VWAP')
line(b.run(base.copy(), max_per_day=3, trail_mode=1, trail_start_R=0.5, trail_param=0.5), 'trail after +0.5R, dist 0.5R')
line(b.run(base.copy(), max_per_day=3, trail_mode=1, trail_start_R=0.5, trail_param=1.0), 'trail after +0.5R, dist 1.0R')
for mbars in (3, 5, 10):  # TF bars (x2 min)
    q = base.copy(); q['tp'] = q.eprice + q.side * 1.0 * (q.eprice - q.sl).abs()
    line(b.run(q, max_per_day=3, max_bars=mbars), f'TP 1R + time exit {mbars*2} min')
    q = base.copy(); q['tp'] = q.eprice + q.side * 0.5 * (q.eprice - q.sl).abs()
    line(b.run(q, max_per_day=3, max_bars=mbars), f'TP 0.5R + time exit {mbars*2} min')
print('\n=== STOP SIZE (ATR stops instead of structural), TP 0.5R / 1R')
for sa in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
    for k_ in (0.5, 1.0):
        q = signals(stop='atr', s_atr=sa); q['tp'] = q.eprice + q.side * k_ * (q.eprice - q.sl).abs()
        line(b.run(q, max_per_day=3), f'stop {sa} ATR, TP {k_}R')
print('\n=== BAND LEVEL / TIME WINDOW (struct stop, TP 1R)')
for k in (2.0, 2.25, 2.5, 2.75, 3.0):
    q = signals(k=k, stop='struct'); q['tp'] = q.eprice + q.side * (q.eprice - q.sl).abs()
    line(b.run(q, max_per_day=3), f'band {k}sd')
q = base.copy(); q['tp'] = q.eprice + q.side * (q.eprice - q.sl).abs()
for a_, z_ in ((720, 840), (840, 960), (720, 810), (810, 900), (900, 960)):
    line(b.run(q, max_per_day=3, ent_start=a_, ent_end=z_), f'window {a_//60}:{a_%60:02d}-{z_//60}:{z_%60:02d}')
