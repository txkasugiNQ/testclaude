"""Phase J: trade-behaviour in candidate windows (what management can exploit).
For IMP / PB events (tf 1,3,5) with a 1-ATR(tf) stop and entry next-bar open:
 speed, first-passage, MFE-before-stop, P(back to entry before +1R | reached +x) [the BE question], MAE needs.
Management convention: a stop move triggered by bar k is active from bar k+1 (bar-close processing).
"""
import numpy as np, pandas as pd
from prep import load
from engine import excursions, outcomes
df = load(); df = df[df.good]
def resample(tf):
    if tf == 1:
        b = df[['sess', 'smin', 'open', 'high', 'low', 'close']].reset_index(drop=True).copy()
    else:
        g = df.assign(k=df.smin // tf).groupby(['sess', 'k'])
        b = g.agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last')).reset_index()
        b['smin'] = b.k * tf
    pc = b.close.shift(1); tr = np.maximum(b.high, pc) - np.minimum(b.low, pc)
    b['atr'] = tr.rolling(20).mean(); return b
def sm(h): a, b_ = map(int, h.split(':')); return (a*60+b_-18*60) % 1440
WINS = {'EU 00:45-02:15': ('00:45', 90), 'NY-AM 09:30-11:30': ('09:30', 120), 'NY-AM 09:45-11:45': ('09:45', 120),
        'NY-MID 12:00-14:30': ('12:00', 150), 'NY-MID 12:15-14:15': ('12:15', 120), 'NY-PM 14:30-16:00': ('14:30', 90),
        'ASIA 20:00-23:00': ('20:00', 180)}
rows = []
for tf in (1, 3, 5):
    b = resample(tf); n = len(b)
    o, h, l, c, atr = (b[k].values for k in ('open', 'high', 'low', 'close', 'atr'))
    ss = b.sess.values.astype('datetime64[D]').astype(np.int64)
    def lag(a, k):
        r = np.full(n, np.nan); r[k:] = a[:-k]; m = np.zeros(n, bool); m[k:] = ss[k:] == ss[:-k]; r[~m] = np.nan; return r
    mv = c - lag(c, 3); imp = np.where(mv >= 1.5 * atr, 1, np.where(mv <= -1.5 * atr, -1, 0))
    mv10 = c - lag(c, 10)
    pb = np.where((lag(c, 1) < lag(o, 1)) & (c > lag(h, 1)) & (mv10 >= 1.5 * atr), 1,
                  np.where((lag(c, 1) > lag(o, 1)) & (c < lag(l, 1)) & (mv10 <= -1.5 * atr), -1, 0))
    A = {'high': h, 'low': l, 'sess': ss, 'close': c, 'open': o}
    H = max(12, 90 // tf)
    rng = np.random.default_rng(1)
    for wname, (st, L) in WINS.items():
        s0 = sm(st)
        inwin = (b.smin.values + tf >= s0 + tf) & (b.smin.values < s0 + L)   # entry bar start inside window
        for trig, s in (('IMP', imp), ('PB', pb), ('CTRL', None)):
            if s is None:
                t = np.flatnonzero(inwin[1:]) ; d = rng.choice([-1, 1], len(t))
            else:
                t = np.flatnonzero((s != 0)[:-1] & inwin[1:]); d = s[t]
            e = t + 1; ok = (ss[e] == ss[t]) & ~np.isnan(atr[t]); t, d, e = t[ok], d[ok], e[ok]
            fav, adv, valid, cl = excursions(A, e, d, o[e], atr[t], H=H, with_close=True)
            out = outcomes(fav, adv, valid, cl)
            j = np.arange(H)[None, :]
            r = {'tf': tf, 'window': wname, 'trig': trig, 'n/day': len(t) / 730, 'R_pts': np.median(atr[t])}
            for a in (0.25, 0.5, 1.0, 2.0):
                w = out[f'win_{a}']; r[f'P+{a}'] = w.mean()
                r[f'min_to_+{a}'] = (np.median(out[f't_{a}'][w]) + 1) * tf if w.any() else np.nan
            r['EV(+1/-1)'] = out['ev_1.0'].mean(); r['EV(+2/-1)'] = out['ev_2.0'].mean()
            for x in (0.2, 0.3, 0.5):
                r[f'MFEpreStop>={x}'] = (out['mfe_pre_stop'] >= x).mean()
            # BE question: reached +x at bar k (before stop); from k+1: back to entry (adv>=0) before +1R?
            for x in (0.15, 0.2, 0.3, 0.5):
                tk = np.where((fav >= x).any(1), (fav >= x).argmax(1), H)
                cand = (tk < out['t_stop']) & (tk < H - 1) & (tk < out['t_1.0'])
                after = j > tk[:, None]
                tbe = np.where(((adv >= 0) & after & valid).any(1), ((adv >= 0) & after & valid).argmax(1), H)
                t1 = np.where(((fav >= 1) & after).any(1), ((fav >= 1) & after).argmax(1), H)
                r[f'P(BE before +1R | +{x})'] = (tbe[cand] <= t1[cand]).mean()
            hit1 = out['t_1.0'] < H
            r['MAEpre+1R_p50'] = np.median(out['mae_pre_1R'][hit1]); r['MAEpre+1R_p75'] = np.quantile(out['mae_pre_1R'][hit1], .75)
            r['MAEpre+1R_p90'] = np.quantile(out['mae_pre_1R'][hit1], .9)
            tres = np.minimum(out['t_stop'], out['t_1.0'])
            r['min_to_resolve(+1/-1)_med'] = (np.median(tres[tres < H]) + 1) * tf
            rows.append(r)
    print('tf', tf, 'done', flush=True)
J = pd.DataFrame(rows); J.to_csv('output/J_behavior.csv', index=False)
pd.set_option('display.width', 400, 'display.max_columns', 60, 'display.max_rows', 200)
for tf in (1, 3, 5):
    print(f'\n######## tf={tf}')
    print(J[J.tf == tf].drop(columns='tf').set_index(['window', 'trig']).round(3).T.to_string())
