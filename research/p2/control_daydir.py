"""Is the H3 result the setup, or just 'trade in the day's direction at midday'? Controls with identical stop+mgmt."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from run_sim import *
from signals import arms_random, entry_machine, TICK
from candidates import T
from grid import mgmt_grid
df = get_df(); c = df.close.values; ro = df.rth_open.values; atr = df.atr20.values

def control_entries(seed, mode, floor, per_day=3.0, win=(T(12, 0), T(14, 30))):
    A = arms_random(df, 5, win[0], win[1] - 15, per_day, seed=seed)
    A['d'] = np.sign(c[A.a.values - 1] - ro[A.a.values - 1]).astype(int)   # day direction at arm time
    A = A[A.d != 0]
    if mode == 'pb':
        E = entry_machine(df, A, win=win)
    else:
        E = pd.DataFrame({'sig': A.a.values - 1, 'd': A.d.values}); E['e'] = E.sig + 1
        E['entry'] = df.open.values[E.e.values]; E['stop'] = np.nan
    s = E.sig.values
    fl = E.entry.values - E.d.values * floor * atr[s]
    E['stop'] = np.where(np.isnan(E.stop.values), fl, np.where(E.d.values > 0, np.minimum(E.stop.values, fl), np.maximum(E.stop.values, fl)))
    E['stop'] = np.where(E.d.values > 0, np.floor(E.stop / TICK) * TICK, np.ceil(E.stop / TICK) * TICK)
    E = E[df.good.values[E.e.values]]
    return E.sort_values('e').reset_index(drop=True)

sel = [m for m in mgmt_grid() if m[1] in ('tp1', 'tp2', '60bars', '120bars', 'be0.2+0.05 act0.3 d0.25', 'be0 act1.0 n10', 'be0 act1.0 3ATR', '0.5@1.0 be_only')]
rows = []
for floor in (1.5, 2.0, 3.0):
    sets = {'H3 setup (pb, day-dir)': [setup_entries('H3', stop_floor_atr=floor)],
            'H3 NO day filter': [setup_entries('H3', stop_floor_atr=floor, day_filter=False)],
            'CTRL random pb day-dir': [control_entries(s, 'pb', floor) for s in range(5)],
            'CTRL random immediate day-dir': [control_entries(s, 'imm', floor, per_day=1.0) for s in range(5)]}
    for name, Es in sets.items():
        for fam, nm, P in sel:
            res = {}
            for per, f in (('IS', lambda y: y <= 2024), ('2023', lambda y: y == 2023), ('2024', lambda y: y == 2024), ('2025', lambda y: y == 2025)):
                vals = [run(E[f(YR[E.e.values])], P).pnl.mean() for E in Es]
                res[per] = np.mean(vals)
            rows.append({'floor': floor, 'set': name, 'mgmt': nm, **res})
    print('floor', floor, flush=True)
R = pd.DataFrame(rows)
pd.set_option('display.width', 250, 'display.max_rows', 300)
print(R.round(3).to_string(index=False))
R.to_csv('../output/p2_control_daydir.csv', index=False)
