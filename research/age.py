from smlab2 import *
for tf in (2,3):
    for age in [0, 3, 5, 10, 15, 20, 30]:
        mins = age*tf
        t = run(tf=tf, entry_mode=1, wait_bars=1, s_stop=1.0, a_pull=0, tp_R=3, min_age=age)
        t2 = run(tf=tf, entry_mode=0, a_pull=0.5, s_stop=0.75, wait_bars=15, tp_R=3, min_age=age)
        print(f'tf{tf} min_age={age}bars({mins}min) | BRK: {summ(t)} | PULL: {summ(t2)}')
