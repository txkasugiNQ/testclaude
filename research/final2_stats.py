from mbl import *
from families3 import _pack_rr
T=mbl(0.12,EOD,cancel=True); T['strat']='MBL'
# best performer: opening bar close-confirmed, |body|>0.03A, stop beyond opening bar, hold to close
i=np.where((m==571)&~np.isnan(A))[0]; i=i[np.abs(c[i]-o[i])>0.03*A[i]]; d=np.sign(c[i]-o[i])
OB=_pack_rr(i,d,np.where(d>0,l[i]-TICK,h[i]+TICK),EOD,0); OB['strat']='OBR'
def show(X,lab):
    s=stats2(X); print(f"{lab:28s} N={s['N']:5d} WR={s['WR']:5.1f} PF={s['PF']:.2f} Exp={s['ExpR']:+.3f}R AvgW={s['AvgWinR']:.2f} AvgL={s['AvgLossR']:.2f} DD={s['MaxDD_R']:5.1f}R LS={s['MaxLS']} WS={s['MaxWS']} TPD(active)={s['TPD']} SharpeD={s['SharpeD']} medR={s['medR']}pts PF_pts={s['PF_pts']}")
D=df.groupby('sd').agg(H=('h','max'),L=('l','min'),A=('atrD','first'))
Rr=df[rth].groupby('sd').agg(rh=('h','max'),rl=('l','min'),ro=('o','first'),rc=('c','last'))
daytype=((Rr.rc-Rr.ro).abs()/(Rr.rh-Rr.rl))   # ex-post: |open->close| / range  (report-only classification)
for X,name in ((T,'MBL'),(OB,'OBR')):
    print(f"\n########## {name}")
    show(X,'ALL 2023-2025')
    for y in (2023,2024,2025): show(X[X.ts.dt.year==y],str(y))
    q=X.groupby(X.ts.dt.to_period('Q')).pnlR.agg(['size','mean','sum']); print("quarters (N/Exp/sumR):"," ".join(f"{p}:{int(r['size'])}/{r['mean']:+.2f}/{r['sum']:+.0f}" for p,r in q.iterrows()))
    si=X.si.values
    X['slot']=pd.cut(m[X.ei.values],[570,600,660,720,780,840,900,961],labels=['09:30','10:00','11:00','12:00','13:00','14:00','15:00'])
    print("by entry hour:",{k:(int(v['size']),round(v['mean'],3)) for k,v in X.groupby('slot',observed=True).pnlR.agg(['size','mean']).iterrows()})
    print("long/short:",{('L' if k>0 else 'S'):(int(v['size']),round(v['mean'],3)) for k,v in X.groupby('dir').pnlR.agg(['size','mean']).iterrows()})
    av=pd.qcut(pd.Series(A[si]).rank(pct=True),3,labels=['lowVol','midVol','highVol']).values
    print("vol tercile:",{k:(int(v['size']),round(v['mean'],3)) for k,v in X.groupby(av,observed=True).pnlR.agg(['size','mean']).iterrows()})
    rg=REG[si]; print("daily regime (prior close vs SMA20):",{('bull' if k==1 else 'bear'):(int(v['size']),round(v['mean'],3)) for k,v in X.groupby(rg).pnlR.agg(['size','mean']).iterrows()})
    dt=pd.cut(X.sd.map(daytype).values,[0,0.3,0.6,1.0],labels=['range day','normal','trend day'])
    print("day type (ex-post, report only):",{k:(int(v['size']),round(v['mean'],3)) for k,v in X.groupby(dt,observed=True).pnlR.agg(['size','mean']).iterrows()})
    X.to_csv(f'final2_trades_{name}.csv',index=False)
# portfolio (two independent position slots, equal 1R risk each)
P=pd.concat([T,OB]).sort_values('ts'); print("\n########## PORTFOLIO MBL+OBR"); show(P,'ALL'); [show(P[P.ts.dt.year==y],str(y)) for y in (2023,2024,2025)]
dm=pd.concat([T.groupby('sd').pnlR.sum().rename('MBL'),OB.groupby('sd').pnlR.sum().rename('OBR')],axis=1).fillna(0); print("daily corr MBL/OBR:",round(dm.corr().iloc[0,1],2))
