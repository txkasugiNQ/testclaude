import pandas as pd, numpy as np
from lab import B
b = B(2)
A = pd.read_pickle('scan3.pkl')
A['day'] = b.day[A.index.values]
for tgt in ['C1.0','C2.0']:
    x = A[A[tgt]!=0]
    d = x.groupby('day')[tgt].apply(lambda s: (s==1).mean())
    for w in [5, 10, 20, 40]:
        trail = d.rolling(w).mean().shift(1)
        m = trail.notna()
        print(tgt, f'w={w}: corr(trailing mean, next day) = {np.corrcoef(trail[m], d[m])[0,1]:+.3f}',
              f' | P(day cont>0.5 | trail>0.5)={((d[m]>0.5)[trail[m]>0.5]).mean():.3f}  P(day cont>0.5 | trail<0.5)={((d[m]>0.5)[trail[m]<0.5]).mean():.3f}')
    print(tgt, 'daily cont rate std', d.std(), 'mean', d.mean(), 'lag1 autocorr', d.autocorr(1))
