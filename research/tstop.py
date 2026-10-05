from smlab2 import *
base = dict(entry_mode=1, wait_bars=1, a_pull=0)
for tf in (2,3):
    for s_ in (1.0,):
        for ex_name, ex in [('TP3', dict(tp_R=3)), ('trail3/1.5', dict(tp_R=0, trail_start_R=3, trail_R=1.5)), ('TP4', dict(tp_R=4))]:
            print(f'tf{tf} stop{s_} {ex_name} no-tstop:', summ(run(tf=tf, s_stop=s_, **base, **ex)))
            for tsb in (5, 10, 15, 20, 30):
                for mr in (0.0, 0.5, 1.0):
                    t = run(tf=tf, s_stop=s_, ts_bars=tsb, ts_minR=mr, **base, **ex)
                    print(f'   tstop {tsb}min minR {mr}: {summ(t)}  avgloss IS {-t[(t.split=="IS")&(t.R<=0)].R.mean():.2f}')
