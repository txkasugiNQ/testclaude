from smlab2 import *
import itertools
base = dict(entry_mode=1, wait_bars=1, a_pull=0)
rows=[]
for tf in (2,3):
  for s_ in (0.75, 1.0, 1.25):
    configs = []
    for k in (2,3,4,6): configs.append((f'TP{k}', dict(tp_R=k)))
    configs.append(('hold', dict(tp_R=0)))
    for ts, td in [(1,1),(1.5,1),(2,1),(2,1.5),(3,1.5),(3,2)]:
        configs.append((f'trail{ts}/{td}', dict(tp_R=0, trail_start_R=ts, trail_R=td)))
    for be in (1.0, 1.5):
        configs.append((f'BE{be}+TP3', dict(tp_R=3, be_R=be)))
        configs.append((f'BE{be}+trail2/1.5', dict(tp_R=0, be_R=be, trail_start_R=2, trail_R=1.5)))
    for pr, pf in [(1,0.5),(1.5,0.5),(2,0.5)]:
        configs.append((f'part{pr}x{pf}+BE+trail2/1.5', dict(tp_R=0, part_R=pr, part_frac=pf, be_R=-1, trail_start_R=2, trail_R=1.5)))
        configs.append((f'part{pr}x{pf}+BE+TP4', dict(tp_R=4, part_R=pr, part_frac=pf, be_R=-1)))
    for name, cfg in configs:
        t = run(tf=tf, s_stop=s_, **base, **cfg)
        r = dict(tf=tf, stop=s_, exit=name)
        for sp in ('IS','VAL'):
            q = t[t.split==sp]; r[f'e_{sp}'] = q.R.mean(); r[f'wr_{sp}'] = (q.R>0).mean(); r[f'n_{sp}'] = len(q)
        rows.append(r)
D = pd.DataFrame(rows); D['min'] = D[['e_IS','e_VAL']].min(axis=1)
pd.set_option('display.width',200); pd.set_option('display.max_rows',500)
print(D.sort_values('min', ascending=False).head(30).round(3).to_string())
D.to_pickle('exits_brk.pkl')
