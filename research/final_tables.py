from validate import *
import json
m = M()
pd.set_option('display.width',220); pd.set_option('display.float_format','{:.3f}'.format)
out = {}
t = final_trades()
T = {}
T['main_precost'] = table(t, m, ['IS','VAL','OOS','IS+VAL'])
T['main_cost'] = table(t, m, ['IS','VAL','OOS','IS+VAL'], cost=True)
# exit variants
ex = {'Fixed TP 4R (selected)': dict(tp_R=4), 'Fixed TP 3R': dict(tp_R=3), 'Fixed TP 2R': dict(tp_R=2),
      'Trailing: start 3R, trail 1.5R': dict(tp_R=0, trail_start_R=3, trail_R=1.5),
      'Trailing: start 2R, trail 1R': dict(tp_R=0, trail_start_R=2, trail_R=1),
      'Hybrid: 50% at 2R + 50% at 4R': dict(tp_R=4, part_R=2, part_frac=0.5),
      'Hybrid: 50% at 1.5R, BE, trail 3R/1.5R': dict(tp_R=0, part_R=1.5, part_frac=0.5, be_R=-1, trail_start_R=3, trail_R=1.5),
      'Time exit only (hold to 16:00)': dict(tp_R=0)}
rows=[]
for k, v in ex.items():
    tt = final_trades(**v)
    for sp in ['IS','VAL','OOS']:
        q = tt[tt.split==sp]; mt = metrics(q, ndays_of(m, sp))
        rows.append(dict(exit=k, split=sp, n=mt['trades'], winrate=mt['winrate'], avg_win_R=mt['avg_win_R'], avg_loss_R=mt['avg_loss_R'],
                         exp_R=mt['expectancy_R'], pf=mt['profit_factor'], maxDD_R=mt['max_dd_R'], maxLS=mt['longest_losing_streak'], dur=mt['avg_dur_min']))
E = pd.DataFrame(rows)
T['exits'] = E.pivot_table(index='exit', columns='split', values=['exp_R','winrate','avg_win_R','pf','maxDD_R','maxLS','dur'])
# by year/side/month
t['yr'] = pd.to_datetime(t.tdate).dt.year
T['by_year'] = t.groupby('yr').R.agg(['mean','count', lambda r:(r>0).mean()]).rename(columns={'<lambda_0>':'wr'})
T['by_side'] = t.groupby(['split','side']).R.agg(['mean','count']).unstack()
T['by_month'] = t.groupby(pd.to_datetime(t.tdate).dt.to_period('M').astype(str)).R.agg(['count','mean','sum'])
# volatility regime: ADR10 tercile (thresholds from IS only)
ro, adr = day_ctx(m, 10)
t['adr'] = adr[t.sig.values]
qs = np.quantile(t[t.split=='IS'].adr, [1/3, 2/3])
t['volreg'] = pd.cut(t.adr, [-np.inf, qs[0], qs[1], np.inf], labels=['low','mid','high'])
T['by_vol'] = t.groupby(['volreg','split'], observed=True).R.agg(['mean','count']).unstack()
# MFE/MAE
T['mfe_mae'] = t.groupby('split')[['mfe','mae']].describe().T
for k, v in T.items():
    print(f'\n######## {k}'); print(v.round(3).to_string() if hasattr(v,'to_string') else v)
pickle_out = {k: v for k, v in T.items()}
pd.to_pickle(pickle_out, 'final_tables.pkl')
print('\nIS ADR terciles (pts):', qs.round(1))
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
os.makedirs(OUT, exist_ok=True)
T['main_precost'].to_csv(f'{OUT}/tdb_metrics_before_costs.csv')
T['main_cost'].to_csv(f'{OUT}/tdb_metrics_after_costs.csv')
E.to_csv(f'{OUT}/tdb_exit_comparison.csv', index=False)
T['by_year'].to_csv(f'{OUT}/tdb_by_year.csv'); T['by_month'].to_csv(f'{OUT}/tdb_by_month.csv'); T['by_side'].to_csv(f'{OUT}/tdb_by_side.csv')
