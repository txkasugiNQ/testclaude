from feats import *
df=build(); rng=np.random.default_rng(0)
ok=np.where(df.rth.values&(df['mod'].values>=600)&(df['mod'].values<=930)&~np.isnan(df.atrD.values))[0]
for kR in [0.02,0.05,0.1,0.2]:
    for d in [1,-1]:
        sig=np.sort(rng.choice(ok,20000,replace=False)); R=kR*df.atrD.values[sig]
        stop=df.c.values[sig]-d*R
        T=run(df,sig,np.full(len(sig),d),stop)
        print(f"R={kR}*atrD dir={d:+d}",stats(T))
