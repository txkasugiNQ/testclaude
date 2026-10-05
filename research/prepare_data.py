"""Step 0: build the cached data files used by every research script (run from this directory).
   python3 prepare_data.py
Creates nq.pkl, nq2.pkl, days.pkl, bars1.pkl, bars2.pkl, bars3.pkl (git-ignored)."""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, '..', 'Dataset_NQ_1min_2022_2025 (1).csv')
df = pd.read_csv(CSV)
df.columns = ['ts','open','high','low','close','volume','vwap_rth','vwap_eth']
df['ts'] = pd.to_datetime(df['ts'], format='%m/%d/%Y %H:%M')     # bar CLOSE time, America/New_York (verified: RTH VWAP starts 09:31 on all days incl. DST changes)
assert df.ts.is_monotonic_increasing and not df.ts.duplicated().any()
df.to_pickle(os.path.join(HERE, 'nq.pkl'))
os.chdir(HERE)
from core import load, day_table
d = load(); d.to_pickle('nq2.pkl')
day_table(d).to_pickle('days.pkl')
from bars import build
for tf in (1, 2, 3): build(tf)
print('data ready')
