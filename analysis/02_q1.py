import pandas as pd, numpy as np
df=pd.read_pickle('nq.pkl')
print(df.dtypes); print(len(df)); print(df.ts.min(), df.ts.max())
print("NaN:\n", df.isna().sum())
print("dup ts:", df.ts.duplicated().sum(), " monotonic:", df.ts.is_monotonic_increasing)
print(df.describe().T)
bad = df[(df.h<df[['o','c','l']].max(axis=1))|(df.l>df[['o','c','h']].min(axis=1))]
print("OHLC inconsistent:", len(bad)); print(bad.head())
print("non-tick multiples:", ((df[['o','h','l','c']]*4)%1!=0).sum().to_dict())
print("zero vol:", (df.v==0).sum(), " neg:", (df.v<0).sum())
print("vr==0 count:", (df.vr==0).sum(), " ve==0:", (df.ve==0).sum())
d=df.ts.diff().dt.total_seconds()/60
print("gap distribution:\n", d.value_counts().head(15))
g=df[d>60][['ts']].assign(gap_min=d[d>60])
print("gaps >60min count:", len(g)); 
# weekend vs other
g['prev']=df.ts.shift()[d>60]
g['dow']=g.ts.dt.dayofweek
print(g.groupby(pd.cut(g.gap_min,[60,70,200,1500,3000,5000,99999])).size())
print(g[g.gap_min>3000].to_string())
print(g[(g.gap_min>70)&(g.gap_min<2800)].to_string())
# minute-of-day coverage
df['tod']=df.ts.dt.hour*60+df.ts.dt.minute
print("hours present:", sorted(df.ts.dt.hour.unique()))
print(df.groupby(df.ts.dt.hour).size())
# returns outliers
r=np.log(df.c).diff()
print("1m abs ret >1%:", (r.abs()>0.01).sum()); print(df.loc[r.abs().nlargest(10).index,['ts','o','h','l','c','v']])
jump=(df.o-df.c.shift()).abs()
print(df.loc[jump.nlargest(10).index,['ts','o','c']].assign(prevc=df.c.shift()[jump.nlargest(10).index], gap=d[jump.nlargest(10).index]))
