import pandas as pd, numpy as np
A = pd.read_pickle('scan3.pkl')
A2 = pd.read_pickle('scan2.pkl')
A = A.join(A2[['bar_rng','ret30','z_vwap','comp10']], how='left')
for f in ['absret5','absret15_aligned','rvol1','rvol5','body_al','bar_rng','zvw_al','comp_pre']:
    x = A[f].replace([np.inf,-np.inf],np.nan)
    for lo, hi in [(0,0.01),(0,0.03),(0.97,1),(0.99,1),(0.995,1)]:
        ql, qh = x.quantile(lo), x.quantile(hi)
        m = (x>=ql)&(x<=qh)
        out=[]
        for sp in ['IS','VAL']:
            for tgt in ['C1.0','C2.0']:
                y = A.loc[m&(A.split==sp), tgt]
                y = y[y!=0]
                out.append(f'{sp} {tgt} cont={(y==1).mean():.2f} n={len(y)}')
        print(f'{f:16s} q[{lo},{hi}] ', ' | '.join(out))
