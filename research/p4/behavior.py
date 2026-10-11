"""Phase 4 step 1: behaviour around the 08:12-09:12 ET range (bar START times 08:12..09:11).
After 09:12: when/how is it broken, and after the FIRST break does price extend (continuation) or come back (reversal)?
First-passage races are measured on 1m bars, conservative ordering does not matter here (descriptive)."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'p3')); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'p2'))
from slots import ctx
c = ctx(); df = c['df']
RS, RE, END = 8 * 60 + 12, 9 * 60 + 12, 15 * 60 + 54
g = df[df.good]
rows = []
for sess, d in g.groupby('sess', sort=True):
    r = d[(d.tod >= RS) & (d.tod < RE)]
    a = d[(d.tod >= RE) & (d.tod <= END)]
    if len(r) < 50 or len(a) < 300: continue
    hi, lo = r.high.max(), r.low.min(); size = hi - lo; mid = (hi + lo) / 2
    H, L, C, T = a.high.values, a.low.values, a.close.values, a.tod.values
    bh = np.flatnonzero(H > hi); bl = np.flatnonzero(L < lo)
    fh = bh[0] if len(bh) else 10**9; fl = bl[0] if len(bl) else 10**9
    row = {'sess': sess, 'hi': hi, 'lo': lo, 'size': size, 'DR': d.DR.iloc[0], 'first': 'none' if min(fh, fl) == 10**9 else ('up' if fh < fl else ('dn' if fl < fh else 'both')),
           'broke_up': len(bh) > 0, 'broke_dn': len(bl) > 0}
    i0 = min(fh, fl)
    if i0 < 10**9 and fh != fl:
        up = fh < fl; row['t_first'] = T[i0]
        edge = hi if up else lo
        # race from the first break bar onward: extension of x*size beyond edge vs return to mid / opposite edge
        ext = (H[i0:] - edge) if up else (edge - L[i0:])          # favourable for continuation
        back = (edge - L[i0:]) if up else (H[i0:] - edge)          # how far back inside, measured from the edge
        for x in (0.25, 0.5, 1.0):
            te = np.flatnonzero(ext >= x * size); tm = np.flatnonzero(back >= 0.5 * size); to = np.flatnonzero(back >= size)
            te = te[0] if len(te) else 10**9; tm = tm[0] if len(tm) else 10**9; to = to[0] if len(to) else 10**9
            row[f'ext{x}_before_mid'] = te < tm if min(te, tm) < 10**9 else np.nan
            row[f'ext{x}_before_opp'] = te < to if min(te, to) < 10**9 else np.nan
        row['max_ext'] = ext.max() / size
        row['ret_mid'] = (back >= 0.5 * size).any(); row['ret_opp'] = (back >= size).any()
        # close-confirmed break: first close beyond edge
        cb = np.flatnonzero(C > hi) if up else np.flatnonzero(C < lo)
        row['closed_beyond'] = len(cb) > 0
    rows.append(row)
B = pd.DataFrame(rows); B['yr'] = pd.DatetimeIndex(B.sess).year
B.to_pickle('../output/p4_behavior.pkl')
print('days', len(B)); print('range size pts median by year:', B.groupby('yr')['size'].median().round(1).to_dict(), ' in DR:', (B['size'] / B.DR).median().round(3))
print('first break side:', B['first'].value_counts(normalize=True).round(3).to_dict())
print('both sides broken same day:', (B.broke_up & B.broke_dn).mean().round(3))
print('first break time distribution:', pd.cut(B.t_first.dropna(), [552, 570, 571, 580, 600, 630, 690, 960], right=False,
      labels=['09:12-09:29', '09:30', '09:31-09:39', '09:40-09:59', '10:00-10:29', '10:30-11:29', '11:30+']).value_counts(normalize=True).sort_index().round(3).to_dict())
for col in ('ext0.25_before_mid', 'ext0.5_before_mid', 'ext1.0_before_mid', 'ext0.5_before_opp', 'ext1.0_before_opp', 'ret_mid', 'ret_opp', 'closed_beyond'):
    print(f'{col:22s}', B[col].astype(float).mean().round(3), ' by year', B.groupby('yr')[col].apply(lambda s: s.astype(float).mean()).round(3).to_dict())
print('max extension beyond edge (x range) quantiles:', B.max_ext.quantile([.25, .5, .75, .9]).round(2).to_dict())
