from validate import *
m = M()
t = final_trades()
t = t[t.split!='OOS']                       # holdout still masked
pd.set_option('display.width',200); pd.set_option('display.float_format','{:.3f}'.format)
print('=== FINAL (pre-registered) — IS / VAL, before costs'); print(table(t, m, ['IS','VAL','IS+VAL']))
print('=== after costs'); print(table(t, m, ['IS','VAL','IS+VAL'], cost=True).loc[['expectancy_R','winrate','profit_factor','max_dd_R']])
print('=== by side'); print(t.groupby(['split','side']).R.agg(['mean','count']).unstack())
q = pd.to_datetime(t.tdate).dt.to_period('Q').astype(str)
print('=== by quarter'); print(t.groupby(q).R.agg(['mean','count']).T.round(2))
print('=== exit reasons'); print(t.groupby('reason').R.agg(['mean','count']))
print('=== entry time buckets'); print(t.groupby(pd.cut(t.etod, [720,750,780,810,845])).R.agg(['mean','count']))
