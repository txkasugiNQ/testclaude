from wf2 import *
tr=pd.read_pickle('tr2_G10_burst_level.pkl')
trs={k:v for k,v in tr.items() if json.loads(k)['entry']=='stop'}
nd=df[df.sd>='2024-01-01'].sd.nunique()
for f in (0.5,1,1.5):
    O,sel=wf(trs,f); s=stats2(O,nd); a=stats2(O)
    print(f"stop-only fmin={f}: N={s['N']} WR={s['WR']} PF={s['PF']} ExpR={s['ExpR']:+.3f} AvgW={s['AvgWinR']} AvgL={s['AvgLossR']} DD={s['MaxDD_R']} MaxLS={s['MaxLS']} MaxWS={s['MaxWS']} SharpeD={s['SharpeD']} TPD={s['TPD']}/{a['TPD']}")
    print("   quarters ExpR:",O.groupby(O.ts.dt.to_period('Q')).pnlR.mean().round(3).tolist())
    for x in sel: print("   ",x[0],x[1][:80],x[4],x[5])
# deployment: same criterion on the last 12 months of data
end=df.sd.max(); start=end-pd.DateOffset(months=12)
ntr=((DAYS>=start)&(DAYS<=end)).sum(); best=None
for k,T in trs.items():
    a=T[(T.sd>=start)]; 
    if len(a)<40 or len(a)/ntr<1: continue
    sc=score(a)
    if best is None or sc>best[0]: best=(sc,k)
print("\nDEPLOY (criterion on last 12 months):",best)
