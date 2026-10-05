from smlab2 import *
def s3(t):
    t = t.assign(yr=pd.to_datetime(t.tdate).dt.year)
    return ' '.join(f'{y}:{t[t.yr==y].R.mean():+.2f}(n={(t.yr==y).sum()},wr={(t[t.yr==y].R>0).mean():.2f})' for y in (2023,2024,2025))
for em in (1, 2):
  for td in (-999, 0.3, 0.5):
    for st in (1.0, 1.5):
      for xn, xc in [('TP2',dict(tp_R=2)),('hold',dict(tp_R=0))]:
        for regf in ['trend','any']:
            kw = {}
            if regf=='any':
                tl = run(tf=2, entry_mode=em, wait_bars=1, a_pull=0, s_stop=st, td_min=td, brk_start=900, brk_end=944, ent_end=946, max_trades=1, allow_short=False, regime_fn=lambda m,r: np.ones(len(r)), **xc)
                ts = run(tf=2, entry_mode=em, wait_bars=1, a_pull=0, s_stop=st, td_min=td, brk_start=900, brk_end=944, ent_end=946, max_trades=1, allow_long=False, regime_fn=lambda m,r: -np.ones(len(r)), **xc)
                t = pd.concat([tl, ts])
            else:
                t = run(tf=2, entry_mode=em, wait_bars=1, a_pull=0, s_stop=st, td_min=td, brk_start=900, brk_end=944, ent_end=946, max_trades=1, **xc)
            print(f'{"BRK" if em==1 else "MKT"} 15:00-15:45 td={td} stop={st} {xn} reg={regf}: {s3(t)}')
