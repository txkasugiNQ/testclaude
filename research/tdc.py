from smlab2 import *
def s3(t):
    t = t.assign(yr=pd.to_datetime(t.tdate).dt.year)
    out=[]
    for y in (2023,2024,2025):
        q=t[t.yr==y]; out.append(f'{y}:{q.R.mean():+.2f}(n={len(q)},wr={(q.R>0).mean():.2f},stop={q.risk.mean():.0f})')
    return ' '.join(out)
for td in (0.3, 0.4, 0.5):
  for st in (1.0, 1.5, 2.0):
    for xn, xc in [('TP2',dict(tp_R=2)),('TP3',dict(tp_R=3)),('tr2/1',dict(tp_R=0,trail_start_R=2,trail_R=1)),('hold',dict(tp_R=0))]:
        t = run(tf=2, entry_mode=2, wait_bars=1, s_stop=st, td_min=td, brk_end=840, ent_end=842, max_trades=1, **xc)
        print(f'TDC market td={td} stop={st} {xn}: {s3(t)}')
