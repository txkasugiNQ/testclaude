"""Chart-shape (motif) discovery on 5-min bars: cluster normalised 24-bar (2h) price shapes, then check
whether any shape is followed by a reliable move. Fit clusters on 2023 only; evaluate 2023 vs 2024 vs 2025."""
from families2 import *
from sklearn.cluster import KMeans
b5=df[rth].set_index('ts')[['o','h','l','c','atrD','vrw']]
B=b5.resample('5min',label='right',closed='right').agg({'o':'first','h':'max','l':'min','c':'last','atrD':'first','vrw':'last'}).dropna()
B['sd']=B.index.normalize()
B=B.reset_index(); B['yr']=B.ts.dt.year; B['mod']=B.ts.dt.hour*60+B.ts.dt.minute
L=24; H=6   # 2h shape, 30-min forward
feats=[];meta=[]
for sd,g in B.groupby('sd'):
    c_=g.c.values; h_=g.h.values; l_=g.l.values; A_=g.atrD.values[0]
    if np.isnan(A_) or len(g)<L+H: continue
    for t in range(L-1,len(g)-H):
        seg=c_[t-L+1:t+1]
        rngs=h_[t-L+1:t+1].max()-l_[t-L+1:t+1].min()
        if rngs<=0: continue
        shape=(seg-seg[-1])/rngs                      # shape normalised by its own range, anchored at current close
        hi_pos=(h_[t-L+1:t+1].argmax())/(L-1); lo_pos=(l_[t-L+1:t+1].argmin())/(L-1)
        feats.append(np.r_[shape,[rngs/A_*2,hi_pos,lo_pos]])
        fw=c_[t+H]-c_[t]                              # forward 30-min move (close to close)
        fh=h_[t+1:t+H+1].max()-c_[t]; fl=c_[t]-l_[t+1:t+H+1].min()
        meta.append((g.ts.values[t],g.yr.values[t],g['mod'].values[t],fw/A_,fh/A_,fl/A_,rngs/A_))
X=np.array(feats); M=pd.DataFrame(meta,columns=['ts','yr','mod','fw','fh','fl','rng'])
tr=M.yr.values==2023
km=KMeans(n_clusters=40,n_init=4,random_state=0).fit(X[tr]); M['cl']=km.predict(X)
# per cluster: mean forward move (ATR %), t-stat, by year; select on 2023 only
rows=[]
for cl,g in M.groupby('cl'):
    r={'cl':cl,'n23':int((g.yr==2023).sum())}
    for y in (2023,2024,2025):
        x=g[g.yr==y].fw; r[f'm{y}']=x.mean()*100; r[f't{y}']=x.mean()/x.std()*np.sqrt(len(x)) if len(x)>10 else np.nan
    rows.append(r)
R=pd.DataFrame(rows).round(2)
sel=R[(R.t2023.abs()>2.5)]
print("clusters with |t|>2.5 in 2023 (fitted & selected on 2023), and their 2024/2025 values:")
print(sel.to_string(index=False))
same=(np.sign(sel.m2024)==np.sign(sel.m2023))&(np.sign(sel.m2025)==np.sign(sel.m2023))
print(f"\nselected: {len(sel)} of 40; same sign in 2024 AND 2025: {same.sum()}  (null ~{len(sel)/4:.1f})")
print("corr of cluster means 2023 vs 2024:",round(np.corrcoef(R.m2023,R.m2024)[0,1],2)," 2023 vs 2025:",round(np.corrcoef(R.m2023,R.m2025)[0,1],2))
pd.to_pickle((km,M,R),'motifs.pkl')
