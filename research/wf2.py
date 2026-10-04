"""Walk-forward v2: objective = expectancy t-stat (ExpR*sqrt(N)/std) on train, with min trades/day."""
from families3 import *
import sys, json, itertools, time
def combos(grid):
    keys=list(grid)
    for vals in itertools.product(*[grid[k] for k in keys]): yield dict(zip(keys,vals))
DAYS=df.groupby('sd').size().index.to_series()
def evaluate(name):
    fn,grid=G[name]; out={}
    for p in combos(grid):
        T=fn(**p)
        if len(T): out[json.dumps(p)]=T
    return out
def score(T):
    r=T.pnlR.values
    return r.mean()/r.std()*np.sqrt(len(r)) if len(r)>2 and r.std()>0 else -9
def wf(trades,fmin,minN=40):
    oos=[];sel=[]
    for tr0,te0,te1 in wf_windows():
        ntr=((DAYS>=tr0)&(DAYS<te0)).sum(); best=None
        for k,T in trades.items():
            a=T[(T.sd>=tr0)&(T.sd<te0)]
            if len(a)<minN or len(a)/ntr<fmin: continue
            s=score(a)
            if best is None or s>best[0]: best=(s,k,a.pnlR.mean(),len(a)/ntr)
        if best is None: continue
        b=trades[best[1]]; b=b[(b.sd>=te0)&(b.sd<te1)]; oos.append(b)
        sel.append((str(te0.date()),best[1],round(best[2],3),round(best[3],2),round(b.pnlR.mean(),3) if len(b) else None,len(b)))
    return (pd.concat(oos) if oos else pd.DataFrame()),sel
if __name__=='__main__':
    nd=df[df.sd>='2024-01-01'].sd.nunique()
    for name in (sys.argv[1:] or list(G)):
        t0=time.time(); tr=evaluate(name); pd.to_pickle(tr,f'tr2_{name}.pkl')
        print(f"\n=== {name}: {len(tr)} combos ({time.time()-t0:.0f}s)")
        for fmin in (0.25,0.5,1,2):
            O,sel=wf(tr,fmin)
            if len(O)==0: print(f" fmin={fmin}: none"); continue
            s=stats2(O,nd); a=stats2(O)
            isx=np.mean([x[2] for x in sel])
            print(f" fmin={fmin}: IS ExpR {isx:+.3f} | OOS N={s['N']} WR={s['WR']} PF={s['PF']} ExpR={s['ExpR']:+.3f} DD={s['MaxDD_R']} MaxLS={s['MaxLS']} SharpeD={s['SharpeD']} TPD(all/active)={s['TPD']}/{a['TPD']}")
