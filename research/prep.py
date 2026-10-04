from engine import *
df=load()
# forced exit index for RTH: bar labelled 16:00 of same session; for ETH: last bar of session
idx=np.arange(len(df)); sd=df.sd.values
last_sess=pd.Series(idx).groupby(sd).transform('max').values
rth_end=df[df['mod']==960].groupby('sd').apply(lambda g:g.index[0])
re=pd.Series(df.sd.map(rth_end)).values
re=np.where(np.isnan(re.astype(float)),last_sess,re).astype(np.int64)
# if bar is after 16:00 the RTH flat index is in the past -> use session end
df['flat_rth']=np.where(idx<=re,re,last_sess)
df['flat_eth']=last_sess
df.to_pickle('bars.pkl'); print(df.tail(2)); print(df.flat_rth.values[:3])
