import pandas as pd, numpy as np, os
SP = os.path.dirname(os.path.abspath(__file__))
IS_END = pd.Timestamp('2024-06-30').date()
VAL_END = pd.Timestamp('2024-12-31').date()

def load():
    df = pd.read_pickle(os.path.join(SP,'nq.pkl'))
    df['tod'] = df.ts.dt.hour*60 + df.ts.dt.minute          # bar CLOSE time in ET minutes
    # trading date: bars after 17:00 belong to next session
    d = df.ts.dt.normalize()
    nxt = df.tod > 17*60
    td = d.where(~nxt, d + pd.Timedelta(days=1))
    # Fri evening doesn't exist; Sun evening -> Mon (sun+1 = Mon OK). Sat? none.
    df['tdate'] = td.dt.date
    return df

def day_table(df):
    """per trading-day levels computed only from data available before 12:00 (and prior day)"""
    g = df.groupby('tdate')
    rows = []
    prev = None
    for td, x in g:
        tod = x.tod.values
        on = x[(tod > 18*60) | (tod <= 9*60+30)]
        rth = x[(tod > 9*60+30) & (tod <= 16*60)]
        am = x[(tod > 9*60+30) & (tod <= 12*60)]
        pm = x[(tod > 12*60) & (tod <= 16*60)]
        r = dict(tdate=td, n=len(x), n_pm=len(pm))
        if len(on): r.update(onh=on.high.max(), onl=on.low.min())
        if len(am):
            r.update(amh=am.high.max(), aml=am.low.min(), rth_open=am.open.iloc[0], am_close=am.close.iloc[-1])
        if len(rth): r.update(rth_h=rth.high.max(), rth_l=rth.low.min(), rth_c=rth.close.iloc[-1])
        if len(pm): r.update(pmh=pm.high.max(), pml=pm.low.min(), pm_open=pm.open.iloc[0], pm_close=pm.close.iloc[-1])
        if prev is not None:
            r.update(pdh=prev.get('rth_h'), pdl=prev.get('rth_l'), pdc=prev.get('rth_c'))
        rows.append(r); prev = r
    t = pd.DataFrame(rows).set_index('tdate')
    return t

def split_of(td):
    return np.where(td <= IS_END, 'IS', np.where(td <= VAL_END, 'VAL', 'OOS'))
