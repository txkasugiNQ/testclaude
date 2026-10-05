from families2 import *
lc=np.log(c)
def ac_by_slot(k):
    # k-minute returns aligned on clock; autocorr of consecutive k-min returns within same session, grouped by slot of the 2nd return
    t=df.ts.values; key=(df.ts.dt.hour*60+df.ts.dt.minute).values
    sel=(key%k==0)
    s=pd.DataFrame({'sd':df.sd.values[sel],'lc':lc[sel],'mod':key[sel],'yr':df.ts.dt.year.values[sel]})
    s['r']=s.groupby('sd').lc.diff(); s['rprev']=s.groupby('sd').r.shift()
    s['slot']=((s['mod']-k)%1440)//30*30   # slot by start of the return interval
    s=s.dropna()
    out={}
    for y in (2023,2024,2025):
        g=s[s.yr==y].groupby('slot')
        out[y]=g.apply(lambda x: np.corrcoef(x.r,x.rprev)[0,1] if len(x)>30 else np.nan)
    O=pd.DataFrame(out); O.index=[f"{i//60:02d}:{i%60:02d}" for i in O.index]; return O
for k in (5,15):
    O=ac_by_slot(k).round(3)
    O['mean']=O.mean(axis=1).round(3); O['same_sign_all_years']=np.sign(O[[2023,2024,2025]]).nunique(axis=1).eq(1)
    print(f"\n=== lag-1 autocorrelation of consecutive {k}-min returns, by 30-min slot (ET) ===")
    print(O.to_string())
