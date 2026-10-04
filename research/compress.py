from families import *
s=f6(th=0.16,stp='sw5',w='all'); T=run(df,s['sig'],s['dir'],s['stop'])
si=T.si.values
for n in (20,30):
    comp=(hhv(h,n)-llv(l,n))/A
    T[f'comp{n}']=comp[si-5]   # measured 5 bars BEFORE the signal (already known then)
T['per']=np.where(T.sd<'2024-01-01','2023','2024-25')
for n in (20,30):
    T['b']=pd.qcut(T[f'comp{n}'],3,labels=['tight','mid','wide'])
    print(f"range of last {n} bars (5 bars before signal), by tercile:")
    print(T.groupby(['b','per'],observed=True).win.agg(['size','mean']).unstack().round(3).to_string())
