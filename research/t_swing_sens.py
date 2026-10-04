from families import *
import engine
# (1) multi-day swing: signal at RTH close (16:00 bar), hold until TP/SL (no time exit except end of data)
idx=np.where((m==960)&~np.isnan(A))[0]
flat_inf=np.full(len(df),len(df)-1,np.int64)
for k in (0.25,0.5,1.0):
    for d in (1,-1):
        st=c[idx]-d*k*A[idx]
        T=run(df,idx,np.full(len(idx),d),st,flat=flat_inf)
        o_=T[T.sd>='2024-01-01']
        print(f"swing R={k}ATR dir={d:+d}: 2023 WR={T[T.sd<'2024-01-01'].win.mean()*100:.1f}  2024-25 WR={o_.win.mean()*100:.1f} N={len(o_)}  TPD={len(o_)/df[df.sd>='2024-01-01'].sd.nunique():.2f}")
# (2) fill/cost sensitivity on random entries (upper bound of what assumptions can do)
rng=np.random.default_rng(1); ok=np.where(win(600,930))[0]; sig=np.sort(rng.choice(ok,20000,replace=False))
for tick,comm,lbl in ((0.25,0.25,'realistic'),(0.0,0.0,'no costs, touch fills')):
    engine.TICK=tick; engine.COMM=comm
    r=engine.simulate(o,h,l,c,sig,np.ones(len(sig)),np.zeros(len(sig),np.int64),np.full(len(sig),np.nan),c[sig]-0.1*A[sig],sig.astype(np.int64),df.flat_rth.values,0.6,tick,comm)
    print(lbl,"random long WR:",round((r[:,4]>0).mean()*100,2))
