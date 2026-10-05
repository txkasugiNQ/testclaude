"""London-session data prep: London-relative minutes for every bar (1m/2m/3m), DST-correct."""
import pandas as pd, numpy as np
for tf in (1, 2, 3):
    x = pd.read_pickle(f'bars{tf}.pkl')
    # reconstruct ET bar-close datetime: tdate + tod minutes (tod is negative for the evening part of the Globex day)
    et = pd.to_datetime(x.tdate.astype(str)) + pd.to_timedelta(x.tod, unit='m')
    et = et.dt.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT')
    ldn = et.dt.tz_convert('Europe/London')
    mid = pd.to_datetime(x.tdate.astype(str)).dt.tz_localize('Europe/London')
    x['ltod'] = ((ldn - mid).dt.total_seconds() / 60).round()       # London minutes of bar CLOSE, relative to London midnight of trading date
    x['et_minus_ldn'] = (x.tod - x.ltod)                             # offset check (normally -300)
    x.to_pickle(f'lbars{tf}.pkl')
    print(tf, x.shape, 'NaT rows', x.ltod.isna().sum(), 'offset counts:', x.et_minus_ldn.value_counts().head(3).to_dict())
x = pd.read_pickle('lbars1.pkl')
# verify DST gap weeks: offset -240 (London 08:00 = 04:00 ET)
g = x[x.et_minus_ldn == -240].tdate.unique()
print('gap-week trading days (London 08:00 = 04:00 ET):', len(g), sorted(map(str, g))[:6], '...', sorted(map(str, g))[-6:])
