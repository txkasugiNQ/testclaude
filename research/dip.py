from cand import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf); L = daylevels(b)
reg = np.nan_to_num(daily_regime(b, 50, 'ma'), nan=0)
c,h,l,atr,tod,vw = b.c,b.h,b.l,b.atr,b.tod,b.vw
rh = L['rh']; rl = L['rl']
win = (tod >= 720 - tf) & (tod < 900)
def summ(t):
    t = t[t.split!='OOS']; out=[]
    for sp in ['IS','VAL']:
        q = t[t.split==sp]; out.append(f'{sp}:{q.R.mean():+.3f}(n={len(q)},wr={(q.R>0).mean():.2f})')
    return ' '.join(out)
print('--- dip from session extreme (limit at extreme - D*ATR), trend aligned')
for D in [2, 3, 4]:
    for S_ in [1.0, 1.5, 2.0]:
        for T in [1.0, 1.5, 2.0, 'ext']:
            rows=[]
            for side in (1,-1):
                X = rh if side>0 else rl
                cond = win & (reg == side)
                idx = np.where(cond)[0]
                e = X[idx] - side*D*atr[idx]
                ok = (c[idx] - e)*side > 0.25
                idx, e = idx[ok], e[ok]
                sl = e - side*S_*atr[idx]
                tp = X[idx] if T=='ext' else e + side*T*atr[idx]
                rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=2, eprice=e, sl=sl, tp=tp, expiry=1)))
            s = pd.concat(rows)
            t = b.run(s, max_per_day=2)
            print(f'D={D} S={S_} T={T}: {summ(t)}')
