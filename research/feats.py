from engine import *
def build():
    p=os.path.join(HERE,'feats.pkl')
    if os.path.exists(p): return pd.read_pickle(p)
    df=load()
    o,h,l,c,v=[df[k].values for k in 'ohlcv']
    g=df.groupby('sd')
    # daily ATR14 (ETH), known before session
    D=pd.DataFrame({'h':g.h.max(),'l':g.l.min(),'c':g.c.last()})
    tr=pd.concat([D.h-D.l,(D.h-D.c.shift()).abs(),(D.l-D.c.shift()).abs()],axis=1).max(axis=1)
    D['atrD']=tr.rolling(14).mean().shift(1)
    df['atrD']=df.sd.map(D.atrD).values
    # 1m true range ATRs
    pc=np.r_[c[0],c[:-1]]; trm=np.maximum(h,pc)-np.minimum(l,pc)
    s=pd.Series(trm)
    for n in (14,60,390): df[f'atr{n}']=s.rolling(n).mean().values
    # RTH vwap + sigma (reset 09:30), ETH vwap + sigma (reset 18:00)
    tp=(h+l+c)/3
    for name,mask,key in (('vr',df.rth.values,df.sd.values),('ve',np.ones(len(df),bool),df.sd.values)):
        vv=np.where(mask,v,0.0); grp=pd.Series(key)
        cv=pd.Series(vv).groupby(grp).cumsum().values; cpv=pd.Series(vv*tp).groupby(grp).cumsum().values
        cp2=pd.Series(vv*tp*tp).groupby(grp).cumsum().values
        with np.errstate(invalid='ignore',divide='ignore'):
            vw=cpv/cv; sdv=np.sqrt(np.maximum(cp2/cv-vw**2,0))
        vw[~mask]=np.nan; sdv[~mask]=np.nan
        df[name+'w']=vw; df[name+'s']=sdv
    # session extremes so far
    df['sh']=g.h.cummax().values; df['sl']=g.l.cummin().values
    r=df.rth.values; key=df.sd.values
    hr=pd.Series(np.where(r,h,-np.inf)).groupby(key).cummax().values
    lr=pd.Series(np.where(r,l,np.inf)).groupby(key).cummin().values
    df['rh']=np.where(r,hr,np.nan); df['rl']=np.where(r,lr,np.nan)
    # EMAs, z-scores, RSI
    cs=pd.Series(c)
    for n in (9,21,50,100,200,500): df[f'ema{n}']=cs.ewm(span=n,adjust=False).mean().values
    for n in (20,60,240):
        m=cs.rolling(n).mean(); sd_=cs.rolling(n).std(); df[f'z{n}']=((cs-m)/sd_).values
    d=cs.diff()
    for n in (14,70):
        up=d.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); dn=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
        df[f'rsi{n}']=(100-100/(1+up/dn)).values
    for k in (5,15,30,60): df[f'ret{k}']=(cs-cs.shift(k)).values
    # prior-day RTH levels
    R=df[r].groupby('sd').agg(ph=('h','max'),pl=('l','min'),pcl=('c','last'))
    for k in ['ph','pl','pcl']: df[k]=df.sd.map(R[k].shift()).values
    # opening range/IB (valid only after formation)
    m=df['mod'].values
    for nmin,name in ((15,'or15'),(30,'or30'),(60,'ib')):
        mask=r&(m<=570+nmin)
        H=pd.Series(np.where(mask,h,np.nan)).groupby(key).transform('max').values
        L=pd.Series(np.where(mask,l,np.nan)).groupby(key).transform('min').values
        ok=r&(m>570+nmin)
        df[name+'h']=np.where(ok,H,np.nan); df[name+'l']=np.where(ok,L,np.nan)
    df.to_pickle(p); return df
if __name__=='__main__':
    df=build(); print(df.columns.tolist()); print(df[df.rth].iloc[5000:5003].T)
