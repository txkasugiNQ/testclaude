import numpy as np, pandas as pd
from lab import B, stats, quarters, split_of
from cand import daily_regime
from sm2 import run_sm2
COLS = ['side','sig','eb','xb','epx','sl','tp','xpx','R','mfe','mae','reason','lvl']
DEF = dict(tf=2, brk_start=720, brk_end=840, ent_end=870, flat_tod=960, a_pull=0.5, s_stop=0.75, wait_bars=15, cancel_atr=2.0,
           tp_R=3.0, max_trades=2, be_R=0.0, trail_start_R=0.0, trail_R=0.0, refresh=True, allow_long=True, allow_short=True,
           min_stop_pts=0.0, part_R=0.0, part_frac=0.0, stop_mode=0, swing_n=5, entry_mode=0, min_age=0, max_age=100000, ts_bars=0, ts_minR=0.0, td_min=-999.0, adr_n=10, reg_w=50, reg_kind='ma', atr_len=14)
_m = {}
def M():
    if 'm' not in _m: _m['m'] = B(1)
    return _m['m']
_reg = {}
_ctx = {}
def day_ctx(m, n):
    if n in _ctx: return _ctx[n]
    d = m.days
    dv = d[d.rth_c.notna() & (d.n_pm >= 200)]
    adr_d = (dv.rth_h - dv.rth_l).rolling(n, min_periods=max(3, n//2)).mean().shift(1)   # prior days only
    ro = pd.Series(m.tdate).map(d.rth_open).values.astype(float)
    ro = np.where(m.tod > 570, ro, np.nan)          # RTH open known only after 9:30
    adr = pd.Series(m.tdate).map(adr_d).values.astype(float)
    _ctx[n] = (ro, adr); return _ctx[n]
def run(**kw):
    p = dict(DEF); p.update(kw)
    m = M()
    key = (p['reg_w'], p['reg_kind'])
    if key not in _reg: _reg[key] = np.nan_to_num(daily_regime(m, p['reg_w'], p['reg_kind']), nan=0.0)
    reg = _reg[key]
    if p.get('regime_fn') is not None: reg = p['regime_fn'](m, reg)
    ro, adr = day_ctx(m, int(p['adr_n']))
    arrs, nt = run_sm2(m.o, m.h, m.l, m.c, m.tod.astype(np.int64), m.day, reg, int(p['tf']), float(p['atr_len']),
                 p['brk_start'], p['brk_end'], p['ent_end'], p['flat_tod'], p['a_pull'], p['s_stop'], int(p['wait_bars']),
                 p['cancel_atr'], p['tp_R'], int(p['max_trades']), p['be_R'], p['trail_start_R'], p['trail_R'],
                 bool(p['refresh']), bool(p['allow_long']), bool(p['allow_short']), p['min_stop_pts'],
                 p['part_R'], p['part_frac'], int(p['stop_mode']), int(p['swing_n']), int(p['entry_mode']), int(p['min_age']), int(p['max_age']), int(p['ts_bars']), float(p['ts_minR']), ro, adr, float(p['td_min']))
    t = pd.DataFrame({k: a[:nt] for k, a in zip(COLS, arrs)})
    t['tdate'] = m.tdate[t.eb.values]; t['split'] = m.split[t.eb.values]
    t['etod'] = m.tod[t.eb.values]; t['xtod'] = m.tod[t.xb.values]; t['stod'] = m.tod[t.sig.values]
    t['risk'] = (t.epx - t.sl).abs(); t['dur'] = (t.xb - t.eb + 1)
    return t
def summ(t, splits=('IS','VAL')):
    out=[]
    for sp in splits:
        q = t[t.split==sp]
        if len(q)==0: out.append(f'{sp}: n=0'); continue
        out.append(f'{sp}:{q.R.mean():+.3f}(n={len(q)},wr={(q.R>0).mean():.2f},risk={q.risk.mean():.1f})')
    return ' '.join(out)
