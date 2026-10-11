"""Truncation test: signals/trades computed on data cut at time X must equal those computed on full data for everything before X."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import candidates
from candidates import get_df
from system import system_entries
from run_sim import run, params
full = get_df().copy()
Ef = system_entries(floor=2.0)
Tf = run(Ef, params(maxbars=60))
rng = np.random.default_rng(5)
cuts = rng.choice(np.flatnonzero((full.smin.values % 15 == 0) & full.good.values & (full.tod.values > 600) & (full.tod.values < 900)), 6, replace=False)
ok = True
for cut in sorted(cuts):
    candidates._df = full.iloc[:cut].copy()        # pretend the future does not exist
    Ec = system_entries(floor=2.0)
    a = Ef[Ef.e < cut - 1][['e', 'd', 'stop']].reset_index(drop=True)
    b = Ec[Ec.e < cut - 1][['e', 'd', 'stop']].reset_index(drop=True)
    same = a.equals(b)
    print('cut', full.ts.iloc[cut], 'entries before cut identical:', same, len(a), len(b))
    ok &= same
candidates._df = full
print('NO LOOK-AHEAD:', ok)
