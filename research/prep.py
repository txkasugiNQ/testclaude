"""Data preparation for NQ 1-min continuation research.

Conventions (no look-ahead):
- CSV label 'timestamp ET' is the bar END time (RTH VWAP starts at label 09:31).
  We convert to bar START time: t_start = label - 1 min. All times below are bar-start ET.
- Exchange timestamps are true US/Eastern, DST handled by the source (17:00-18:00 break constant).
- Trading session D = bars from 18:00 ET (D-1) to 16:59 ET (D).
- smin = minutes since 18:00 session open (0..1379).
"""
import numpy as np, pandas as pd, os

CSV = os.path.join(os.path.dirname(__file__), '..', 'Dataset_NQ_1min_2022_2025 (1).csv')
CACHE = os.path.join(os.path.dirname(__file__), 'output', 'nq_prep.pkl')
TICK = 0.25

def load():
    if os.path.exists(CACHE):
        return pd.read_pickle(CACHE)
    df = pd.read_csv(CSV)
    ts = pd.to_datetime(df['timestamp ET'], format='%m/%d/%Y %H:%M') - pd.Timedelta(minutes=1)
    df = df.drop(columns=['timestamp ET']).assign(ts=ts)
    tod = ts.dt.hour * 60 + ts.dt.minute
    df['tod'] = tod                                   # minutes since midnight ET (bar start)
    df['smin'] = (tod - 18 * 60) % 1440               # minutes since 18:00
    sess = ts.dt.normalize() + pd.to_timedelta((tod >= 18 * 60).astype(int), unit='D')
    df['sess'] = sess
    # true range & ATR (causal; includes overnight bars, that's past data)
    pc = df['close'].shift(1)
    tr = np.maximum(df['high'], pc) - np.minimum(df['low'], pc)
    tr = tr.fillna(df['high'] - df['low'])
    df['tr'] = tr
    df['atr20'] = tr.rolling(20, min_periods=20).mean()
    # session quality: drop half days / broken sessions
    g = df.groupby('sess')
    info = pd.DataFrame({'n': g.size(), 'last': g['tod'].max(), 'first_s': g['smin'].min()})
    good = info[(info['n'] >= 1300) & (info['last'] >= 16 * 60 + 50)].index
    df['good'] = df['sess'].isin(good)
    df = df[df['sess'] >= '2023-01-01'].reset_index(drop=True)
    df.to_pickle(CACHE)
    return df

if __name__ == '__main__':
    df = load()
    print(df.head()); print(len(df), df['sess'].nunique(), df[df.good]['sess'].nunique())
    print(df.groupby(df.sess.dt.year)['sess'].nunique())
