"""Load the immutable CSV once, convert to bar-OPEN time (TradingView convention),
add trading-day / session columns, store as pickle for later scripts.
The CSV itself is never modified."""
import pandas as pd, numpy as np
SRC = "../Dataset_NQ_1min_2022_2025 (1).csv"
df = pd.read_csv(SRC)
df["ts_close"] = pd.to_datetime(df["timestamp ET"], format="%m/%d/%Y %H:%M")
df["t"] = df["ts_close"] - pd.Timedelta(minutes=1)          # bar OPEN time (TV `time`)
df = df.drop(columns=["timestamp ET"]).sort_values("t").reset_index(drop=True)
assert df["t"].is_unique
# CME trading day: starts 18:00 ET. Label = calendar date of the session's close.
td = (df["t"] + pd.Timedelta(hours=6)).dt.normalize()
df["tday"] = td
df["mod"] = df["t"].dt.hour * 60 + df["t"].dt.minute      # minute-of-day (open time, ET)
df.to_pickle("data_1m.pkl")
print(df.head(3)); print(df.tail(3)); print(len(df))
# integrity
g = df.groupby("tday").size()
print("sessions", len(g), "bars/session describe\n", g.describe())
print("short sessions (<1300 bars):\n", g[g < 1300])
gaps = df["t"].diff().dt.total_seconds().div(60)
big = df.loc[gaps > 1, ["t"]].assign(gap_min=gaps[gaps > 1])
print("gaps >1min (excluding the daily 17:00-18:00 break and weekends):")
print(big[~big.gap_min.isin([61])].query("gap_min < 2000").to_string()[:3000])
print("OHLC sanity", ((df.high < df[["open","close"]].max(axis=1)) | (df.low > df[["open","close"]].min(axis=1))).sum())
print("tick grid", (np.mod(df[["open","high","low","close"]].values*4,1)!=0).sum())
