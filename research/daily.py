import pandas as pd, numpy as np
from core import *
df = pd.read_pickle('nq2.pkl'); t = pd.read_pickle('days.pkl')
t = t[t.n > 1000].copy()
piv = df[df.tdate.isin(t.index)].pivot_table(index='tdate', columns='tod', values='close')
vw = df[df.tdate.isin(t.index)].pivot_table(index='tdate', columns='tod', values='vwap_rth')
t['p12'] = piv[720]; t['p16'] = piv[960]; t['vw12'] = vw[720]
t = t[t.n_pm==240]
t['pm'] = t.p16 - t.p12
# daily features using only prior days and AM
t['ret1'] = t.rth_c.shift(1) - t.rth_c.shift(2)
t['ret5'] = t.rth_c.shift(1) - t.rth_c.shift(6)
t['ret20'] = t.rth_c.shift(1) - t.rth_c.shift(21)
t['ma20'] = t.rth_c.shift(1).rolling(20).mean()
t['hi20'] = t.rth_h.shift(1).rolling(20).max(); t['lo20'] = t.rth_l.shift(1).rolling(20).min()
t['gap'] = t.rth_open - t.pdc
t['am'] = t.p12 - t.rth_open
t['vs_pdc'] = t.p12 - t.pdc
t['vs_ma20'] = t.p12 - t.ma20
t['pos20'] = (t.p12 - t.lo20)/(t.hi20 - t.lo20)
t['vs_vw'] = t.p12 - t.vw12
t['dow'] = pd.to_datetime(t.index).dayofweek
t['above_pdh'] = (t.p12 > t.pdh).astype(int) - (t.p12 < t.pdl).astype(int)
t['sp'] = split_of(t.index.values)
t = t[t.sp!='OOS']
for f in ['ret1','ret5','ret20','gap','am','vs_pdc','vs_ma20','pos20','vs_vw','dow','above_pdh']:
    line=[]
    for s in ['IS','VAL']:
        x = t[t.sp==s]
        if f in ('dow','above_pdh'):
            g = x.groupby(f).pm.agg(lambda r: (r>0).mean()); line.append(' '.join(f'{k}:{v:.2f}' for k,v in g.items()))
        else:
            g = x.groupby(pd.qcut(x[f], 3, labels=False)).pm.agg(lambda r: (r>0).mean()); line.append(' '.join(f'{v:.2f}' for v in g))
    print(f'{f:10s} P(PM up) by tercile  IS: {line[0]} | VAL: {line[1]}')
print('base', t.groupby('sp').pm.agg(lambda r: (r>0).mean()))
print('-----')
t['adr'] = (t.rth_h - t.rth_l).shift(1).rolling(10).mean()
t['z'] = t.vs_pdc / t.adr
t['zg'] = t.gap / t.adr
for f in ['z','zg']:
    for s in ['IS','VAL']:
        x = t[t.sp==s]
        print(f, s, 'corr(sign) %.3f' % np.corrcoef(x[f].fillna(0), x.pm)[0,1], ' agree %.3f' % (np.sign(x[f])==np.sign(x.pm)).mean())
        for thr in [0.25, 0.5, 0.75]:
            up = x[x[f] > thr]; dn = x[x[f] < -thr]
            print(f'   thr {thr}: P(up|z>thr)={ (up.pm>0).mean():.2f} n={len(up)} meanPM={up.pm.mean():+.1f} | P(dn|z<-thr)={(dn.pm<0).mean():.2f} n={len(dn)} meanPM={dn.pm.mean():+.1f}')
