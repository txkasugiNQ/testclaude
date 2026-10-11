"""Variant: overnight/London range must be INTACT at 09:30 (no 1m close beyond it between range end and 09:30);
then trade the first 1m close beyond it in [09:30, we). Range [rs, re)."""
import numpy as np, pandas as pd, sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))
from orb import mats, sm, hm, run, params, TICK

def rth_break_entries(rs, re, we, k=0.15, intact=True, min_dr=0.03, entry_from='09:30'):
    M = mats(); C, Hh, Ll, I, DR = M['C'].values, M['H'].values, M['L'].values, M['I'].values, M['DR']
    a, b, o, w = sm(hm(rs)), sm(hm(re)), sm(hm(entry_from)), sm(hm(we))
    hi = np.nanmax(Hh[:, a:b], axis=1); lo = np.nanmin(Ll[:, a:b], axis=1)
    pre = C[:, b:o]
    broken_pre = ((pre > hi[:, None]) | (pre < lo[:, None])).any(1) if o > b else np.zeros(len(hi), bool)
    win = C[:, o:w]; up = win > hi[:, None]; dn = win < lo[:, None]; brk = up | dn
    j = np.argmax(brk, axis=1); has = brk.any(1)
    ok = has & np.isfinite(DR) & np.isfinite(hi)
    if intact: ok &= ~broken_pre
    out = []
    for r in np.flatnonzero(ok):
        jj = j[r]; col = o + jj; d = 1 if up[r, jj] else -1
        sig = I[r, col]
        if not np.isfinite(sig) or col + 1 >= 1380 or not np.isfinite(I[r, col + 1]): continue
        cl = C[r, col]; st = cl - d * k * DR[r]
        lim = cl - d * min_dr * DR[r]; st = min(st, lim) if d > 0 else max(st, lim)
        st = np.floor(st / TICK) * TICK if d > 0 else np.ceil(st / TICK) * TICK
        out.append((int(sig) + 1, int(sig), d, st, DR[r], (hi[r] - lo[r]) / DR[r], col))
    return pd.DataFrame(out, columns=['e', 'sig', 'd', 'stop', 'DR', 'rng_dr', 'col'])

if __name__ == '__main__':
    rows = []
    for rs, re, we, intact in itertools.product(('00:00', '01:00', '02:00', '03:00', '18:00'), ('07:00', '08:00', '08:30', '09:00', '09:30'),
                                                ('10:00', '10:30', '11:00', '11:30', '12:00', '13:00'), (True, False)):
        if re == '09:30' and not intact: continue
        for k in (0.08, 0.1, 0.12, 0.15, 0.2):
            E = rth_break_entries(rs, re, we, k=k, intact=intact)
            Tt = run(E, params(maxbars=1000))
            r = {'rs': rs, 're': re, 'we': we, 'intact': intact, 'k': k, 'n/day': len(Tt) / 730, 'exp': Tt.pnl.mean(), 'WR': (Tt.pnl > 1e-9).mean()}
            for y in (2023, 2024, 2025): r[y] = Tt[Tt.yr == y].pnl.mean()
            rows.append(r)
    R = pd.DataFrame(rows); R['min_y'] = R[[2023, 2024, 2025]].min(axis=1)
    R.to_pickle('../output/p3_rthbreak.pkl')
    pd.set_option('display.width', 250, 'display.max_rows', 300)
    for it in (True, False):
        s = R[R.intact == it]
        print(f'==== intact={it}: {len(s)} configs, all-years-positive {(s.min_y > 0).mean():.2f}, median exp {s.exp.median():.3f}, median n/day {s["n/day"].median():.2f}')
        for col in ('rs', 're', 'we', 'k'):
            print(s.groupby(col)[['exp', 'min_y', 'n/day']].median().round(3).T.to_string())
    print(R[(R.rs == '02:00') & (R.re == '08:00') & R.intact].round(3).to_string(index=False))
