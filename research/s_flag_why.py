from structlib import *
W=win(575,930)
P,F,X,q=20,15,0.2,0.4
fh=hhv(h,F); fl=llv(l,F); ph_=prev(hhv(h,P),F); pl_=prev(llv(l,P),F); pc=prev(c,F); pole=ph_-pl_
up=(pole>=X*A)&(pc>=pl_+0.7*pole)&((fh-fl)<=q*pole)&(fl>=ph_-0.5*pole)
dn=(pole>=X*A)&(pc<=ph_-0.7*pole)&((fh-fl)<=q*pole)&(fh<=pl_+0.5*pole)
trL=W&(prev(up.astype(float))==1)&(c>prev(fh)); trS=W&(prev(dn.astype(float))==1)&(c<prev(fl))
i=np.r_[np.where(trL)[0],np.where(trS)[0]]; d=np.r_[np.ones(trL.sum()),-np.ones(trS.sum())]
ent=c[i]; stop=np.where(d>0,prev(fl)[i]-TICK,prev(fh)[i]+TICK); b=np.abs(ent-stop)
r,mae,mfe=first_hit(h,l,i.astype(np.int64),d,ent,b.copy(),b,flat)
T=pd.DataFrame({'yr':YR[i],'win':r>0,'dec':r!=0,'hour':(m[i]-1)//60,'dir':np.where(d>0,'long','short'),
                'atrQ':pd.qcut(pd.Series(A[i]).rank(pct=True),3,labels=['lowATR','midATR','highATR']).values,
                'vr':np.where(df.atr60.values[i]/df.atr390.values[i]<1,'calm','excited'),
                'reg':np.where(REG[i]==1,'bull','bear'),'vw':np.where(np.sign(c[i]-vrw[i])==d,'with VWAP','against VWAP')})
T=T[T.dec]
for col in ('hour','dir','atrQ','vr','reg','vw'):
    print(f"\n-- by {col} (P(+1R before -1R); RW=0.50) --")
    print(T.pivot_table(index=col,columns='yr',values='win',aggfunc=['mean','size']).round(2).to_string())
