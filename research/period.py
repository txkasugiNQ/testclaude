import pandas as pd, numpy as np
from core import *
df = pd.read_pickle('nq2.pkl'); t = pd.read_pickle('days.pkl')
good = t.index[t.n_pm==240]
piv = df[df.tdate.isin(good)].pivot_table(index='tdate', columns='tod', values='close')
sp = pd.Series(split_of(piv.index.values), index=piv.index)
slots = list(range(720, 960, 30))
R = pd.DataFrame({s: piv[s+30]-piv[s] for s in slots})
for w in [5, 10, 20, 60]:
    tr = R.rolling(w).mean().shift(1)
    out=[]
    for s_ in ['IS','VAL']:
        m = (sp==s_) & tr.notna().all(axis=1)
        x = tr[m].values.ravel(); y = R[m].values.ravel()
        out.append(f'{s_}: corr={np.corrcoef(x,y)[0,1]:+.3f} signagree={(np.sign(x)==np.sign(y)).mean():.3f}')
    print(f'w={w}', ' | '.join(out))
print(R[sp=='IS'].mean().round(2).to_dict()); print(R[sp=='VAL'].mean().round(2).to_dict())
