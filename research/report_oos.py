from validate import *
m = M()
t = final_trades()
t.to_pickle('final_trades.pkl')
pd.set_option('display.width',200); pd.set_option('display.float_format','{:.3f}'.format)
print('=== FINAL (pre-registered) — before costs'); print(table(t, m, ['IS','VAL','OOS','IS+VAL']))
print('=== after costs'); print(table(t, m, ['IS','VAL','OOS'], cost=True).loc[['expectancy_R','winrate','profit_factor','max_dd_R','total_R']])
o = t[t.split=='OOS']
print('=== OOS by side'); print(o.groupby('side').R.agg(['mean','count']))
print('=== OOS by month'); print(o.groupby(pd.to_datetime(o.tdate).dt.to_period('M').astype(str)).R.agg(['mean','count','sum']).T.round(2))
