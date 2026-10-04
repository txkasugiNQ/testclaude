from families import *
import sys, json, itertools, time
def combos(grid):
    keys=list(grid); 
    for vals in itertools.product(*[grid[k] for k in keys]): yield dict(zip(keys,vals))
def evaluate_family(name,fmins=(0.2,0.5,1,2)):
    fn,grid=FAM[name]; trades={}
    for p in combos(grid):
        s=fn(**p)
        if s is None or len(s['sig'])==0: continue
        T=run(df,s['sig'],s['dir'],s['stop'],etype=s.get('etype'),epx=s.get('epx'),expiry=s.get('expiry'))
        if len(T): trades[json.dumps(p)]=T
    return trades
def wf_select(trades,fmin,minN=40):
    sel=[];oos=[]
    days=df.groupby('sd').size().index.to_series()
    for tr0,te0,te1 in wf_windows():
        ntr=((days>=tr0)&(days<te0)).sum()
        best=None
        for k,T in trades.items():
            Ttr=T[(T.sd>=tr0)&(T.sd<te0)]
            if len(Ttr)<minN or len(Ttr)/ntr<fmin: continue
            wr=Ttr.win.mean(); ex=Ttr.pnlR.mean()
            score=(round(wr,3),ex)
            if best is None or score>best[0]: best=(score,k,wr,len(Ttr)/ntr)
        if best is None: sel.append(None); continue
        T=trades[best[1]]; Tte=T[(T.sd>=te0)&(T.sd<te1)]
        oos.append(Tte); sel.append((str(te0.date()),best[1],round(best[2]*100,1),round(best[3],2),round(Tte.win.mean()*100,1),len(Tte)))
    O=pd.concat(oos) if oos else pd.DataFrame()
    return O,sel
if __name__=='__main__':
    names=sys.argv[1:] or list(FAM)
    nd_oos=df[(df.sd>='2024-01-01')].sd.nunique()
    for name in names:
        t0=time.time(); trades=evaluate_family(name)
        # in-sample view: best combo on full 2023 (exploration window)
        print(f"\n=== {name}: {len(trades)} combos, {time.time()-t0:.0f}s")
        for fmin in (0.2,0.5,1,2):
            O,sel=wf_select(trades,fmin)
            if len(O)==0: print(f" fmin={fmin}: no eligible combos"); continue
            st=stats(O,days=nd_oos)
            isw=np.mean([s[2] for s in sel if s]) if any(sel) else np.nan
            print(f" fmin={fmin}: IS(train avg) WR={isw:.1f} | WF-OOS {st}")
        pd.to_pickle(trades,f'tr_{name}.pkl')
