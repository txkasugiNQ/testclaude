from wf import *
import json
tr=pd.read_pickle('tr_F6b_mom_refined.pkl')
for fmin in (1,2):
    O,sel=wf_select(tr,fmin)
    print(f"fmin={fmin}"); [print(" ",s) for s in sel]
    print(" WF-OOS:",stats(O,df[df.sd>='2024-01-01'].sd.nunique()))
# fixed-param plateau: OOS WR 2024-25 by params (no selection)
rows=[]
for k,T in tr.items():
    p=json.loads(k); a=T[T.sd<'2024-01-01']; b=T[T.sd>='2024-01-01']
    rows.append({**p,'WR23':a.win.mean()*100,'TPD23':len(a)/252,'WR2425':b.win.mean()*100,'TPD2425':len(b)/490})
R=pd.DataFrame(rows)
print("corr WR23/WR2425:",round(R[['WR23','WR2425']].corr().iloc[0,1],2))
for p in ['n','th','tf','vf','stp','w']: print(p,R.groupby(p).WR2425.mean().round(1).to_dict())
print(R[R.TPD23>=2].sort_values('WR23',ascending=False).head(8).round(2).to_string(index=False))
