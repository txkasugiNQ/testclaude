from lab import *
exec(open('h5.py').read().split('for conf in')[0].replace("tf = int(sys.argv[1]) if len(sys.argv)>1 else 2","tf=2"))
allsig = []
for name, X, side in [('amh',L['amh'],1),('aml',L['aml'],-1),('onh',L['onh'],1),('onl',L['onl'],-1),('pdh',L['pdh'],1),('pdl',L['pdl'],-1)]:
    s = break_retest(X, side, 0.5, 1.0, 30); s['lev']=name; allsig.append(s)
sig = pd.concat(allsig)
for name in ['amh','aml','onh','onl','pdh','pdl']:
    ladder(b, sig[sig.lev==name], ks=(1,2,3), label=f'level {name}', max_per_day=3)
s2 = sig.copy(); s2['tp'] = np.nan
for ts, tp in [(1,1),(1,0.5),(1.5,1),(2,1)]:
    t = b.run(s2, trail_mode=1, trail_start_R=ts, trail_param=tp, max_per_day=3)
    report(t, b, f'trail start {ts}R dist {tp}R')
for k in [2,3]:
    t = b.run(s2, trail_mode=2, trail_start_R=1, trail_param=k, max_per_day=3)
    report(t, b, f'trail candle-low {k} bars after 1R')
t = b.run(s2, max_per_day=3)
report(t, b, 'hold to 16:00 (no target)')
print(t.groupby('split')[['mfe','mae']].describe().T)
