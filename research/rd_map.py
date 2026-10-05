import sys
from rangelib import *
years=tuple(int(x) for x in sys.argv[1].split(',')) if len(sys.argv)>1 else (2023,)
build_all()
for nm,R in RANGES.items():
    yy=YR[R[:,3].astype(int)]; k=np.isin(yy,years)
    print(f"{nm:30s} ranges={k.sum():5d}  median width {np.median((R[k,0]-R[k,1])):.0f} pts = {np.median((R[k,0]-R[k,1])/A[R[k,3].astype(int)]):.2f} ATR")
rows=[]
for nm in RANGES:
    for k in (0.0,0.25,0.5,1.0,1.5,2.0):
        ev=events(nm,k)
        if ev is None: continue
        t,lv,d,W=ev; sel=np.isin(YR[t],years); t,lv,d,W=t[sel],lv[sel],d[sel],W[sel]
        if len(t)<40: continue
        nr=len(RANGES[nm][np.isin(YR[RANGES[nm][:,3].astype(int)],years)])
        r={'range':nm,'k':k,'touch%':round(len(t)/(2*nr)*100,0),'N':len(t)}
        for lab,s in (('0.5W',0.5*W),('0.1ATR',0.1*A[t])):
            cr,rr,mfe,mae=touch_outcomes(o,h,l,c,t,lv,d,s,s,flat,TICK)
            r[f'CONT {lab}']=round(np.mean(cr[cr!=0]>0),3); r[f'REV {lab}']=round(np.nanmean(rr[(rr!=0)&~np.isnan(rr)]>0),3)
        r['MFE/W']=round(np.median(mfe/W),2); r['MAE/W']=round(np.median(mae/W),2)
        rows.append(r)
T=pd.DataFrame(rows); pd.set_option('display.width',250); print(T.to_string(index=False)); T.to_csv(f'rd_map_{"_".join(map(str,years))}.csv',index=False)
