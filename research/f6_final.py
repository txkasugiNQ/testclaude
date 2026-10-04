from wf import *
import json
tr=pd.read_pickle('tr_F6_mom_burst.pkl'); nd=df[df.sd>='2024-01-01'].sd.nunique()
for fmin in (1,2):
    O,sel=wf_select(tr,fmin); print(f"F6 fmin={fmin}"); [print(" ",s) for s in sel]; print(" WF-OOS",stats(O,nd))
rows=[]
for k,T in tr.items():
    p=json.loads(k); a=T[T.sd<'2024-01-01']; b=T[T.sd>='2024-01-01']
    q=b.groupby(b.ts.dt.to_period('Q')).win.mean()*100
    rows.append({**p,'WR23':a.win.mean()*100,'TPD23':len(a)/252,'WR2425':b.win.mean()*100,'TPD2425':len(b)/nd,'PF2425':b.pnlR[b.pnlR>0].sum()/-b.pnlR[b.pnlR<0].sum(),'Qmin':q.min(),'Qmax':q.max()})
R=pd.DataFrame(rows).round(2); print(R.sort_values('WR2425',ascending=False).to_string(index=False))
