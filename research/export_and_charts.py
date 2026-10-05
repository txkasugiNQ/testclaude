from validate import *
from lab import B, daylevels
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, os
m = M(); t = final_trades()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results'); os.makedirs(OUT, exist_ok=True); os.makedirs(OUT+'/charts', exist_ok=True)
ts = pd.read_pickle('nq2.pkl')[['ts']]   # not aligned; build timestamps from tdate/tod
def ts_of(i):
    d = pd.Timestamp(m.tdate[i]); tod = int(m.tod[i])
    return d + pd.Timedelta(minutes=tod)
rsn = {1:'SL',2:'TP',3:'Time 16:00',4:'Trail/BE stop',5:'Time stop'}
E = pd.DataFrame(dict(
    trade_date=t.tdate.astype(str), split=t.split, side=np.where(t.side>0,'LONG','SHORT'),
    signal_bar_close_ET=[ts_of(i).strftime('%Y-%m-%d %H:%M') for i in t.sig],
    entry_bar_close_ET=[ts_of(i).strftime('%Y-%m-%d %H:%M') for i in t.eb],
    exit_bar_close_ET=[ts_of(i).strftime('%Y-%m-%d %H:%M') for i in t.xb],
    entry=t.epx.round(2), stop=t.sl.round(2), target=t.tp.round(2), exit=t.xpx.round(2),
    risk_pts=t.risk.round(2), R=t.R.round(3), exit_reason=t.reason.map(rsn), mfe_R=t.mfe.round(3), mae_R=t.mae.round(3), duration_min=t.dur))
E.to_csv(OUT+'/tdb_trades_python_reference.csv', index=False)
print('trades exported', len(E))
# volatility regime as % of price (ADR10 / price), terciles from IS
ro, adr = day_ctx(m, 10)
t['adr_pct'] = adr[t.sig.values] / m.c[t.sig.values] * 100
qs = np.quantile(t[t.split=='IS'].adr_pct, [1/3, 2/3])
t['vol'] = pd.cut(t.adr_pct, [-np.inf, qs[0], qs[1], np.inf], labels=['low','mid','high'])
V = t.groupby(['vol','split'], observed=True).R.agg(['mean','count']).unstack()
print('ADR% terciles (IS):', qs.round(3)); print(V.round(3))
V.to_csv(OUT+'/tdb_by_vol_regime.csv')
# ---------------- example charts ----------------
b2 = B(2)
L2 = daylevels(b2)
def chart(k, fn):
    r = t.iloc[k]; d = r.tdate
    sel = (b2.tdate == d) & (b2.tod > 570) & (b2.tod <= 960)
    idx = np.where(sel)[0]
    x = b2.tod[idx]
    fig, ax = plt.subplots(figsize=(18,8))
    for i, xx in zip(idx, x):
        up = b2.c[i] >= b2.o[i]; col = '#26a69a' if up else '#ef5350'
        ax.vlines(xx, b2.l[i], b2.h[i], color=col, lw=0.8)
        ax.add_patch(plt.Rectangle((xx-0.7, min(b2.o[i], b2.c[i])), 1.4, max(abs(b2.c[i]-b2.o[i]), 0.25), color=col))
    i_s = r.sig; ro_ = ro[i_s]; ad = adr[i_s]; sd = r.side
    ax.axhline(ro_, color='gray', ls='-.', lw=1); ax.text(575, ro_, 'RTH open', color='gray', fontsize=9, va='bottom')
    ax.axhline(ro_ + sd*0.4*ad, color='purple', ls='--', lw=1); ax.text(575, ro_ + sd*0.4*ad, 'trend-day threshold (open ± 0.4·ADR10)', color='purple', fontsize=9, va='bottom')
    ext = L2['rh'][idx] if sd>0 else L2['rl'][idx]
    ax.step(x, ext, where='post', color='green' if sd>0 else 'red', lw=1.2, label='running session high' if sd>0 else 'running session low')
    ax.axvspan(720, 842, color='yellow', alpha=0.08, label='setup window 12:00-14:00')
    et = int(m.tod[r.eb]); xt = int(m.tod[r.xb]); st_ = int(m.tod[r.sig])
    ax.axvline(st_, color='orange', lw=0.8, ls=':'); ax.text(st_, ax.get_ylim()[1], ' setup armed', color='orange', fontsize=9, va='top')
    ax.hlines(r.epx, et-1, xt, color='blue', lw=2, label='entry')
    ax.hlines(r.sl, et-1, xt, color='red', lw=2, label='stop-loss')
    ax.hlines(r.tp, et-1, xt, color='green', lw=2, label='take-profit 4R')
    ax.scatter([et-0.5], [r.epx], marker='^' if sd>0 else 'v', s=180, color='teal' if sd>0 else 'maroon', zorder=5)
    ax.text(et, r.epx, ('  BUY ' if sd>0 else '  SELL ')+f'{r.epx:.2f}', fontsize=10, color='blue', va='bottom' if sd>0 else 'top')
    ax.scatter([xt], [r.xpx], marker='X', s=140, color='black', zorder=5)
    ax.text(xt, r.xpx, f'  exit {rsn[r.reason]} {r.R:+.2f}R', fontsize=10)
    ax.set_xticks(range(570, 961, 30)); ax.set_xticklabels([f'{v//60}:{v%60:02d}' for v in range(570, 961, 30)])
    ax.set_title(f'TDB example — {d} ({r.split}) {"LONG" if sd>0 else "SHORT"}  risk={r.risk:.1f} pts  result={r.R:+.2f}R   [2m candles; execution on 1m]')
    ax.legend(loc='best', fontsize=8); ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(fn, dpi=70); plt.close(fig)
picks = []
for sp in ['IS','VAL','OOS']:
    q = t[t.split==sp]
    w = q[q.R>0]; lo = q[q.R<=0]
    if len(w): picks.append(w.index[len(w)//2])
    if len(lo): picks.append(lo.index[len(lo)//2])
for k in picks:
    r = t.loc[k]
    chart(t.index.get_loc(k), f'{OUT}/charts/tdb_{r.split}_{r.tdate}_{"win" if r.R>0 else "loss"}.png')
print(os.listdir(OUT+'/charts'))
