from validate import *
m = M()
def s3(t):
    out=[]
    for sp in ['IS','VAL','OOS']:
        q=t[t.split==sp]; out.append(f'{sp}:{q.R.mean():+.2f}(n={len(q)},wr={(q.R>0).mean():.2f})')
    return ' '.join(out)
base = dict(PAR)
print('final           ', s3(final_trades()))
print('no trend-day flt', s3(final_trades(td_min=-999)))
print('TP2             ', s3(final_trades(tp_R=2)))
print('TP1             ', s3(final_trades(tp_R=1)))
print('hold            ', s3(final_trades(tp_R=0)))
print('no regime long  ', s3(final_trades(regime_fn=lambda m,r: np.ones(len(r)), allow_short=False)))
print('no regime short ', s3(final_trades(regime_fn=lambda m,r: -np.ones(len(r)), allow_long=False)))
print('fade (opposite side: short new highs on trend-up)', '-> see next')
# path stats for OOS vs IS: P(reach +kR before -1R) for the final entries
t = final_trades(tp_R=0)
from path import path_stats
ks = np.array([0.5,1,2,3,4])
mb, tr, mfe, mae, fin = path_stats(m.h, m.l, m.c, m.tod, m.day, t.eb.values.astype(np.int64), t.side.values.astype(np.int64), t.epx.values, t.risk.values, ks, 960)
for sp in ['IS','VAL','OOS']:
    msk = (t.split==sp).values
    row = [((~np.isnan(mb[msk,j])) & (mb[msk,j] < 1)).mean() for j in range(len(ks))]
    print(sp, 'P(+kR before -1R):', ' '.join(f'{k}:{p:.2f}' for k,p in zip(ks,row)), ' MAE median', np.median(mae[msk]).round(2), ' final median', np.median(fin[msk]).round(2))
