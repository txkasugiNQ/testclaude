from rangelib import *
build_all()
rows=[]
for nm in RANGES:
    R=RANGES[nm].astype(np.float64)
    for mode,lab in ((0,'C close-beyond -> CONT'),(1,'E sweep&reclaim -> REV')):
        for k in (0.0,0.25,0.5,1.0,1.5):
            ev=close_events(h,l,c,R,float(k),mode,10)
            if len(ev)<60: continue
            E=np.array(ev); t=E[:,0].astype(np.int64); d=E[:,1]; W=E[:,2]
            ok=~np.isnan(A[t]); t,d,W=t[ok],d[ok],W[ok]
            r={'range':nm,'mech':lab,'k':k}
            for s_lab,s in (('0.1A',0.1*A[t]),('0.5W',0.5*W)):
                res=sym_from_close(o,h,l,c,t,d,s,flat)
                for y in (2023,2024,2025):
                    kk=(YR[t]==y)&(res!=0)
                    r[f'{s_lab}_{y}']=round((res[kk]>0).mean(),3) if kk.sum()>=25 else np.nan
            r['N/yr']=int(len(t)/3)
            rows.append(r)
T=pd.DataFrame(rows); T.to_csv('rd_map2.csv',index=False)
T['min3_0.1A']=T[['0.1A_2023','0.1A_2024','0.1A_2025']].min(axis=1); T['min3_0.5W']=T[['0.5W_2023','0.5W_2024','0.5W_2025']].min(axis=1)
pd.set_option('display.width',260); pd.set_option('display.max_rows',300)
print(T.sort_values('min3_0.1A',ascending=False).to_string(index=False))
