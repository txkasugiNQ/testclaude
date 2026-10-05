import pandas as pd, numpy as np, os
from core import *
def build(tf):
    fn = f'bars{tf}.pkl'
    if os.path.exists(fn): return pd.read_pickle(fn)
    df = pd.read_pickle('nq2.pkl')
    # use RTH-anchored session minutes; bucket label = ceil(tod/tf)*tf  (bar close label)
    # handle overnight: tod > 17:00 -> shift by -1440 so that day is continuous
    m = df.tod.where(df.tod <= 17*60, df.tod - 1440)
    b = ((m - 1)//tf + 1)*tf
    df['b'] = b
    g = df.groupby(['tdate','b'], sort=True)
    out = pd.DataFrame(dict(o=g.open.first(), h=g.high.max(), l=g.low.min(), c=g.close.last(),
                            v=g.volume.sum(), vw=g.vwap_rth.last(), n=g.open.size())).reset_index()
    out.rename(columns={'b':'tod'}, inplace=True)
    out.to_pickle(fn)
    return out
if __name__=='__main__':
    for tf in (1,2,3):
        x = build(tf); print(tf, x.shape, x.head(2).to_dict('records'))
