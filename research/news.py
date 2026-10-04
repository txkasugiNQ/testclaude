from evstudy import *
a14=df.atr14.values
rows=[]; add=lambda r: rows.append(r) if r else None
# impulse bar at fixed minute (bar starting at HH:MM -> close-time mod = start+1); follow its direction from next open
for start,name in ((510,'08:30'),(570,'09:30'),(600,'10:00'),(840,'14:00'),(950,'15:50')):
    for k in (0,0.03,0.06):
        i=np.where((m==start+1)&~np.isnan(A))[0]; mv=(c[i]-o[i])/A[i]
        sel=np.abs(mv)>k; 
        for yrs in ((2023,),(2024,),(2025,)):
            r=study(f'{name} bar |mv|>{k} follow {yrs[0]}',i[sel],np.sign(mv[sel]),years=yrs,hz=(5,15,30,60))
            add(r)
R=pd.DataFrame(rows); pd.set_option('display.width',250); print(R.to_string(index=False))
