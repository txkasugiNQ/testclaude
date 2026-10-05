from smlab2 import *
import itertools, time
rows=[]; t0=time.time()
exits = [('TP2',dict(tp_R=2)),('TP3',dict(tp_R=3)),('TP4',dict(tp_R=4)),('tr2/1',dict(tp_R=0,trail_start_R=2,trail_R=1)),
         ('tr2/1.5',dict(tp_R=0,trail_start_R=2,trail_R=1.5)),('tr3/1.5',dict(tp_R=0,trail_start_R=3,trail_R=1.5)),
         ('tr3/2',dict(tp_R=0,trail_start_R=3,trail_R=2)),('hold',dict(tp_R=0))]
stops = [('atr0.75',dict(stop_mode=0,s_stop=0.75)),('atr1.0',dict(stop_mode=0,s_stop=1.0)),('atr1.25',dict(stop_mode=0,s_stop=1.25)),('atr1.5',dict(stop_mode=0,s_stop=1.5)),
         ('sw3',dict(stop_mode=1,swing_n=3,s_stop=0.1)),('sw5',dict(stop_mode=1,swing_n=5,s_stop=0.1))]
for tf in (2,3):
    for be in (780, 810, 840, 870):
        for sn, sc in stops:
            for xn, xc in exits:
                t = run(tf=tf, entry_mode=1, wait_bars=1, a_pull=0, brk_end=be, ent_end=be+tf, **sc, **xc)
                r = dict(tf=tf, brk_end=be, stop=sn, exit=xn)
                for sp in ('IS','VAL'):
                    q = t[t.split==sp]; r[f'e_{sp}']=q.R.mean(); r[f'n_{sp}']=len(q); r[f'wr_{sp}']=(q.R>0).mean(); r[f'risk_{sp}']=q.risk.mean()
                q = t[t.split!='OOS']; r['e_pool'] = q.R.mean()
                rows.append(r)
    print(tf, len(rows), f'{time.time()-t0:.0f}s', flush=True)
G = pd.DataFrame(rows); G['min'] = G[['e_IS','e_VAL']].min(axis=1)
G.to_pickle('grid_brk.pkl')
pd.set_option('display.width',220); pd.set_option('display.max_rows',100)
print(G.sort_values('min', ascending=False).head(40).round(3).to_string())
