from families import *
import json
tr=pd.read_pickle('tr_F14_impulse_retrace_limit.pkl')
rows=[]
for k,T in tr.items():
    p=json.loads(k); a=T[T.sd<'2024-01-01']; b=T[T.sd>='2024-01-01']
    rows.append({**p,'N23':len(a),'WR23':a.win.mean()*100,'N2425':len(b),'WR2425':b.win.mean()*100,'PF2425':b.pnlR[b.pnlR>0].sum()/-b.pnlR[b.pnlR<0].sum()})
R=pd.DataFrame(rows).round(1)
print("Fixed-parameter view (no selection) — sorted by WR 2023 (what a researcher would pick):")
print(R.sort_values('WR23',ascending=False).head(12).to_string(index=False))
print("\ncorrelation WR23 vs WR2425 across combos:",round(R[['WR23','WR2425']].corr().iloc[0,1],2))
print("\nmarginal means of WR2425 per param:")
for p in ['n','th','ret','kst','tf','w']: print(p, R.groupby(p).WR2425.mean().round(1).to_dict())
