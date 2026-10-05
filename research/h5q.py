from lab import *
exec(open('h5.py').read().split('for conf in')[0].replace("tf = int(sys.argv[1]) if len(sys.argv)>1 else 2","tf=2"))
allsig = []
for name, X, side in [('amh',L['amh'],1),('aml',L['aml'],-1),('onh',L['onh'],1),('onl',L['onl'],-1),('pdh',L['pdh'],1),('pdl',L['pdl'],-1)]:
    s = break_retest(X, side, 0.5, 1.0, 30); s['lev']=name; allsig.append(s)
sig = pd.concat(allsig)
t = b.run(sig, max_per_day=3)
q = quarters(t); print('hold-to-close by quarter'); print(q.round(3).T)
print('long vs short', t[t.split!='OOS'].groupby(['split','side']).R.agg(['mean','count']))
s2 = sig.copy(); s2['tp'] = s2.eprice + s2.side*2*(s2.eprice-s2.sl).abs()
t = b.run(s2, max_per_day=3); print('2R by quarter'); print(quarters(t).round(3).T)
