"""Gold-standard lookahead test: run the engine on data truncated at bar T and compare every event with
bar < T against the full-history run. Any difference would prove use of future data."""
import pandas as pd, numpy as np
from engine import *
df = pd.read_pickle("data_1m.pkl")
b = make_bars(df, 1)
full = pd.read_pickle("events_1m.pkl")
for T in [150_000, 333_333]:
    ev, _, _ = run_engine(b.iloc[:T].reset_index(drop=True))
    f = full[full.bar < T - 1].drop(columns=["split"]).reset_index(drop=True)
    e = ev[ev.bar < T - 1].reset_index(drop=True)
    same = (len(f) == len(e)) and np.allclose(f.values.astype(float), e.values.astype(float), equal_nan=True)
    print(f"T={T}: events full={len(f)} truncated={len(e)} identical={same}")
