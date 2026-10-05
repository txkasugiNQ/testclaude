import pandas as pd, numpy as np
from core import *
df = pd.read_pickle('nq2.pkl'); t = pd.read_pickle('days.pkl')
t = t[(t.n_pm==240)]
t = t[t.index<=IS_END]
# price at specific times
piv = df[df.tdate.isin(t.index)].pivot_table(index='tdate', columns='tod', values='close')
vw = df[df.tdate.isin(t.index)].pivot_table(index='tdate', columns='tod', values='vwap_rth')
p = lambda m: piv[m]
am_move = p(720) - t.rth_open
pm_move = p(960) - p(720)
print('N days', len(t))
print('corr AM move vs PM move', np.corrcoef(am_move, pm_move)[0,1])
for a,b,c in [(720,780,960),(720,810,960),(780,840,960),(720,900,960),(840,900,960),(900,930,960),(720,840,900)]:
    x = p(b)-p(a); y = p(c)-p(b)
    print(f'corr move {a//60}:{a%60:02d}-{b//60}:{b%60:02d} vs -> {c//60}:{c%60:02d}: {np.corrcoef(x,y)[0,1]:.3f}  sign agree {(np.sign(x)==np.sign(y)).mean():.3f}')
# vwap side at 12:00 vs PM move
side = np.sign(p(720) - vw[720])
print('PM move by VWAP side at 12:00:', pm_move.groupby(side).agg(['mean','median','count']))
print('PM move by AM move sign:', pm_move.groupby(np.sign(am_move)).agg(['mean','median','count']))
# AM range breaks in PM
brk_h = t.pmh > t.amh; brk_l = t.pml < t.aml
print('P(break AMH)',brk_h.mean(),'P(break AML)',brk_l.mean(),'both',(brk_h&brk_l).mean(),'none',(~brk_h&~brk_l).mean())
print('break AMH given above vwap', brk_h[side>0].mean(), 'given below', brk_h[side<0].mean())
print('break AML given above vwap', brk_l[side>0].mean(), 'given below', brk_l[side<0].mean())
amr = t.amh - t.aml; pmr = t.pmh - t.pml
print('AM range', amr.describe()); print('PM range', pmr.describe())
print('corr AMr PMr', np.corrcoef(amr,pmr)[0,1])
# extension beyond AMH when broken
ext_h = (t.pmh - t.amh)[brk_h]; ext_l = (t.aml - t.pml)[brk_l]
print('ext beyond AMH when broken', ext_h.describe()); print('ext beyond AML', ext_l.describe())
# distance of 12:00 price to AMH/AML as frac of AM range
pos = (p(720)-t.aml)/amr
print('pos in AM range at 12:00', pos.describe())
print('break AMH by pos tercile', brk_h.groupby(pd.qcut(pos,3)).mean())
print('break AML by pos tercile', brk_l.groupby(pd.qcut(pos,3)).mean())
