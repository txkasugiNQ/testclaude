from wf2 import *
tr=pd.read_pickle('tr2_G7_opening_bar.pkl'); nd=df[df.sd>='2024-01-01'].sd.nunique()
O,sel=wf(tr,0.25)
for s in sel: print(s)
print("quarters:",O.groupby(O.ts.dt.to_period('Q')).pnlR.agg(['size','sum']).round(1).T.to_string())
# outlier dependence: PF without top 5 / top 10 trades
r=O.pnlR.sort_values(ascending=False)
for k in (0,5,10,20):
    x=r.iloc[k:]; print(f"drop top {k}: PF {x[x>0].sum()/-x[x<0].sum():.2f} ExpR {x.mean():+.3f}")
rows=[]
for k,T in tr.items():
    p=json.loads(k); a=T[T.sd<'2024-01-01']; b=T[T.sd>='2024-01-01']
    pf=lambda x: x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum() if (x.pnlR<0).any() else np.nan
    rows.append({**p,'N23':len(a),'PF23':pf(a),'Exp23':a.pnlR.mean(),'N2425':len(b),'PF2425':pf(b),'Exp2425':b.pnlR.mean(),'WR2425':b.win.mean()*100})
R=pd.DataFrame(rows).round(2); pd.set_option('display.width',250)
print(R.sort_values('PF2425',ascending=False).to_string(index=False))
