from wf2 import *
tr=pd.read_pickle('tr2_G10_burst_level.pkl'); rows=[]
for k,T in tr.items():
    p=json.loads(k); r={}
    for lab,(a,b) in (('23',('2022-12-01','2024-01-01')),('24',('2024-01-01','2025-01-01')),('25',('2025-01-01','2026-01-01'))):
        x=T[(T.sd>=a)&(T.sd<b)]; r['PF'+lab]=round(x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum(),2); r['N'+lab]=len(x)
    rows.append({**{kk:p[kk] for kk in ('th','w','ex','entry')},**r})
R=pd.DataFrame(rows); R['minPF']=R[['PF23','PF24','PF25']].min(axis=1); print(R.sort_values('minPF',ascending=False).to_string(index=False))
