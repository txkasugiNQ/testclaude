from smlab2 import *
import time
rows=[]; t0=time.time()
exits = [('TP2',dict(tp_R=2)),('TP2.5',dict(tp_R=2.5)),('TP3',dict(tp_R=3)),('TP4',dict(tp_R=4)),
         ('tr2/1',dict(tp_R=0,trail_start_R=2,trail_R=1)),('tr3/1.5',dict(tp_R=0,trail_start_R=3,trail_R=1.5)),('tr3/2',dict(tp_R=0,trail_start_R=3,trail_R=2)),
         ('p1.5h+BE+tr3/1.5',dict(tp_R=0,part_R=1.5,part_frac=0.5,be_R=-1,trail_start_R=3,trail_R=1.5)),
         ('p2h+TP4',dict(tp_R=4,part_R=2,part_frac=0.5)), ('hold',dict(tp_R=0))]
stops = [0.75, 1.0, 1.25]
tds = [0.3, 0.35, 0.4, 0.45, 0.5]
for tf in (2,3):
    for be in (810, 840, 870):
        for st in stops:
            for td in tds:
                for xn, xc in exits:
                    t = run(tf=tf, entry_mode=1, wait_bars=1, a_pull=0, brk_end=be, ent_end=be+tf, s_stop=st, td_min=td, **xc)
                    r = dict(tf=tf, brk_end=be, stop=st, td=td, exit=xn)
                    for sp in ('IS','VAL'):
                        q = t[t.split==sp]; r[f'e_{sp}']=q.R.mean(); r[f'n_{sp}']=len(q); r[f'wr_{sp}']=(q.R>0).mean()
                    q = t[t.split!='OOS']; r['e_pool']=q.R.mean(); r['wr_pool']=(q.R>0).mean(); r['n_pool']=len(q)
                    rows.append(r)
    print(tf, len(rows), f'{time.time()-t0:.0f}s', flush=True)
G = pd.DataFrame(rows); G['min'] = G[['e_IS','e_VAL']].min(axis=1)
G.to_pickle('grid_td.pkl')
