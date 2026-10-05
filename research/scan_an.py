import pandas as pd, numpy as np
F = pd.read_pickle('scan2.pkl')
F = F[F['L1.5'].notna()]
feats = [c for c in F.columns if c not in ('split','L1.5','S1.5','L3.0','S3.0')]
pd.set_option('display.width', 250)
for mult in ['1.5','3.0']:
    print('==== mult', mult, ' baseline long win', (F[f'L{mult}']==1).mean(), 'short win', (F[f'S{mult}']==1).mean())
    for f in feats:
        x = F[f].replace([np.inf,-np.inf], np.nan)
        q = pd.qcut(x.rank(method='first'), 10, labels=False)
        out=[]
        for sp in ['IS','VAL']:
            m = F.split==sp
            lw = (F.loc[m, f'L{mult}']==1).groupby(q[m]).mean()
            sw = (F.loc[m, f'S{mult}']==1).groupby(q[m]).mean()
            out.append((lw, sw))
        lw_is, sw_is = out[0]; lw_v, sw_v = out[1]
        mx = max(lw_is.max(), sw_is.max())
        print(f'{f:12s} L_IS ' + ' '.join(f'{v:.2f}' for v in lw_is) + ' | L_VAL ' + ' '.join(f'{v:.2f}' for v in lw_v))
        print(f'{"":12s} S_IS ' + ' '.join(f'{v:.2f}' for v in sw_is) + ' | S_VAL ' + ' '.join(f'{v:.2f}' for v in sw_v))
