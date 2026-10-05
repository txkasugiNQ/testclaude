import pandas as pd, numpy as np
from core import *
df = pd.read_pickle('nq2.pkl'); t = pd.read_pickle('days.pkl')
t = t[(t.n_pm==240)]
piv = df[df.tdate.isin(t.index)].pivot_table(index='tdate', columns='tod', values='close')
sp = pd.Series(split_of(piv.index.values), index=piv.index)
p = lambda m: piv[m]
op = t.rth_open.reindex(piv.index); pdc = t.pdc.reindex(piv.index)
for name, x, y in [('open->15:30 vs 15:30->16', p(930)-op, p(960)-p(930)),
                   ('pdc->15:30 vs 15:30->16', p(930)-pdc, p(960)-p(930)),
                   ('open->15:00 vs 15:00->16', p(900)-op, p(960)-p(900)),
                   ('pdc->10:00 vs 15:30->16', p(600)-pdc, p(960)-p(930)),
                   ('12->15:30 vs 15:30->16', p(930)-p(720), p(960)-p(930)),
                   ('open->14:00 vs 14:00->16', p(840)-op, p(960)-p(840)),
                   ('open->13:00 vs 13:00->16', p(780)-op, p(960)-p(780)),
                   ('open->12:00 vs 12:00->16', p(720)-op, p(960)-p(720)),
                   ('15:00->15:45 vs 15:45->16', p(945)-p(900), p(960)-p(945)),
                   ]:
    out=[]
    for s in ['IS','VAL','OOS']:
        m = sp==s
        out.append(f'{s}: corr={np.corrcoef(x[m],y[m])[0,1]:+.3f} agree={(np.sign(x[m])==np.sign(y[m])).mean():.3f} meanSigned={np.mean(np.sign(x[m])*y[m]):+.2f}')
    print(name.ljust(28), ' | '.join(out))
