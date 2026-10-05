import json, numpy as np, pandas as pd
from smlab2 import run, M, day_ctx
P = json.load(open('PREREG.json'))
PAR = P['params']; COST = P['cost_model']
def costs_pts(t):
    c = np.full(len(t), COST['commission_rt_pts'] + COST['entry_stop_slip_pts'])
    r = t.reason.values
    c += np.where((r==1)|(r==4), COST['stop_exit_slip_pts'], 0.0)
    c += np.where(r==2, COST['tp_limit_slip_pts'], 0.0)
    c += np.where((r==3)|(r==5), COST['time_exit_slip_pts'], 0.0)
    return c
def metrics(t, ndays, cost=False):
    if len(t)==0: return {}
    r = t.R.values - (costs_pts(t)/t.risk.values if cost else 0)
    w = r > 0
    gw = r[w].sum(); gl = -r[~w].sum()
    eq = np.cumsum(r); dd = (np.maximum.accumulate(np.r_[0,eq])[1:] - eq).max()
    st=[]; cur=0
    for x in r:
        if x<=0: cur+=1
        else:
            if cur: st.append(cur); cur=0
    if cur: st.append(cur)
    return dict(trades=len(r), trades_per_day=len(r)/ndays, winrate=w.mean(), avg_win_R=r[w].mean() if w.any() else 0,
                avg_loss_R=-r[~w].mean() if (~w).any() else 0, expectancy_R=r.mean(), profit_factor=gw/gl if gl>0 else np.inf,
                max_dd_R=dd, longest_losing_streak=max(st) if st else 0, avg_losing_streak=np.mean(st) if st else 0,
                total_R=r.sum(), avg_stop_pts=t.risk.mean(), median_stop_pts=t.risk.median(), avg_dur_min=t.dur.mean(),
                avg_MFE_R=t.mfe.mean(), avg_MAE_R=t.mae.mean(), avg_win_pts=(t.R*t.risk)[t.R>0].mean(),
                tstat=r.mean()/(r.std(ddof=1)/np.sqrt(len(r))) if len(r)>2 else np.nan)
def ndays_of(m, sp):
    return np.unique(m.tdate[m.split==sp]).size if sp!='ALL' else np.unique(m.tdate).size
def table(t, m, splits, cost=False):
    rows={}
    for sp in splits:
        if sp=='IS+VAL': q=t[t.split.isin(['IS','VAL'])]; nd=ndays_of(m,'IS')+ndays_of(m,'VAL')
        else: q=t[t.split==sp]; nd=ndays_of(m,sp)
        rows[sp]=metrics(q, nd, cost)
    return pd.DataFrame(rows)
def final_trades(**over):
    p = dict(PAR); p.update(over)
    return run(**p)
