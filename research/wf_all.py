from wf import *
import glob
allT={}
for f in sorted(glob.glob('tr_F*.pkl')):
    fam=f[3:-4]
    for k,T in pd.read_pickle(f).items(): allT[fam+'|'+k]=T
print("total combos:",len(allT))
nd=df[df.sd>='2024-01-01'].sd.nunique()
rows=[]
for fmin in (0.1,0.2,0.5,1,2,3,5):
    O,sel=wf_select(allT,fmin,minN=30)
    st=stats(O,nd); isw=np.mean([s[2] for s in sel if s])
    fams=sorted(set(s[1].split('|')[0] for s in sel if s))
    rows.append(dict(fmin=fmin,IS_WR=round(isw,1),**{k:st[k] for k in ['N','WR','PF','ExpR','MaxDD_R','MaxLS','TPD']},families=','.join(fams)))
    q=O.groupby(O.ts.dt.to_period('Q')).win.mean().round(3)*100
    rows[-1]['WR_by_quarter']=' '.join(f"{x:.0f}" for x in q.values)
R=pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv('tradeoff_all.csv',index=False)
