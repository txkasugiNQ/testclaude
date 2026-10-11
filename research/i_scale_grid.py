"""Phase I: start x length grid of continuation edge on 3/5/15-min structure (IMP + PB), per year.
Same definitions as h_scale.py. Windows restricted to 00:00-16:30 ET to avoid the 18:00 ATR carry-over artifact.
"""
import numpy as np, pandas as pd
from prep import load
from engine import excursions, outcomes
df = load(); df = df[df.good]
def resample(tf):
    g = df.assign(k=df.smin // tf).groupby(['sess', 'k'])
    b = g.agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last')).reset_index()
    b['smin'] = b.k * tf
    pc = b.close.shift(1); tr = np.maximum(b.high, pc) - np.minimum(b.low, pc)
    b['atr'] = tr.rolling(20).mean(); return b
def lbl(sm): t = (18*60+sm) % 1440; return f'{t//60:02d}:{t%60:02d}'
res = []
for tf in (1, 3, 5, 15):
    b = resample(tf); n = len(b)
    o, h, l, c, atr = (b[k].values for k in ('open', 'high', 'low', 'close', 'atr'))
    ss = b.sess.values.astype('datetime64[D]').astype(np.int64)
    def lag(a, k):
        r = np.full(n, np.nan); r[k:] = a[:-k]; m = np.zeros(n, bool); m[k:] = ss[k:] == ss[:-k]; r[~m] = np.nan; return r
    mv = c - lag(c, 3)
    imp = np.where(mv >= 1.5 * atr, 1, np.where(mv <= -1.5 * atr, -1, 0))
    mv10 = c - lag(c, 10)
    pb = np.where((lag(c, 1) < lag(o, 1)) & (c > lag(h, 1)) & (mv10 >= 1.5 * atr), 1,
                  np.where((lag(c, 1) > lag(o, 1)) & (c < lag(l, 1)) & (mv10 <= -1.5 * atr), -1, 0))
    A = {'high': h, 'low': l, 'sess': ss, 'close': c, 'open': o}
    def run(t, d, name):
        e = t + 1; ok = (e < n); ok[ok] &= ss[np.minimum(e, n-1)][ok] == ss[t[ok]]; ok &= ~np.isnan(atr[t])
        t, d, e = t[ok], d[ok], e[ok]
        H = max(10, 60 // tf); fr = []
        for s0 in range(0, len(t), 300000):
            sl = slice(s0, s0 + 300000)
            fav, adv, valid, cl = excursions(A, e[sl], d[sl], o[e[sl]], atr[t[sl]], H=H, with_close=True)
            r = outcomes(fav, adv, valid, cl)
            fr.append(pd.DataFrame({'trig': name, 'sm': b.smin.values[e[sl]], 'yr': pd.DatetimeIndex(b.sess.values[t[sl]]).year,
                             'w0.5': r['ev_0.5'], 'w1': r['ev_1.0'], 'w2': r['ev_2.0']}))
        return pd.concat(fr)
    allt = np.arange(n - 1)
    X = pd.concat([run(np.flatnonzero(imp), imp[imp != 0], 'IMP'), run(np.flatnonzero(pb), pb[pb != 0], 'PB'),
                   run(allt, np.ones(len(allt), int), 'CTRL'), run(allt, -np.ones(len(allt), int), 'CTRL')])
    S = X.groupby(['trig', 'yr', 'sm'])[['w0.5', 'w1', 'w2']].agg(['sum', 'count'])
    S.columns = ['_'.join(x) for x in S.columns]; S = S.reset_index()
    for s in range(360, 1350, 15):           # 00:00 .. 16:30
        for L in (30, 45, 60, 90, 120, 150, 180):
            if s + L > 1380: continue
            w = S[(S.sm >= s) & (S.sm < s + L)]
            for trig in ('IMP', 'PB'):
                r = {'tf': tf, 'trig': trig, 'start': lbl(s), 'sm': s, 'len': L}
                for y in (2023, 2024, 2025, 'all'):
                    wy = w if y == 'all' else w[w.yr == y]
                    ev, ct = wy[wy.trig == trig], wy[wy.trig == 'CTRL']
                    for k in ('w0.5', 'w1', 'w2'):
                        r[f'{k}_{y}'] = ev[k + '_sum'].sum() / max(ev[k + '_count'].sum(), 1) - ct[k + '_sum'].sum() / ct[k + '_count'].sum()
                    r[f'n_{y}'] = ev['w1_count'].sum()
                r['w1_min'] = min(r['w1_2023'], r['w1_2024'], r['w1_2025'])
                r['w2_min'] = min(r['w2_2023'], r['w2_2024'], r['w2_2025'])
                res.append(r)
    print('tf', tf, 'done', flush=True)
R = pd.DataFrame(res); R.to_pickle('output/I_grid_ev.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 300)
cols = ['tf', 'trig', 'start', 'len', 'n_all', 'w0.5_all', 'w1_all', 'w1_2023', 'w1_2024', 'w1_2025', 'w1_min', 'w2_all', 'w2_min']
for tf in (1, 3, 5, 15):
    for trig in ('IMP', 'PB'):
        r = R[(R.tf == tf) & (R.trig == trig) & (R.n_all >= 300)]
        print(f'=== tf {tf} {trig}: top 15 by min-year EV-edge (bracket +1R/-1R, in R) ===')
        print(r.sort_values('w1_min', ascending=False)[cols].head(15).round(3).to_string(index=False))
