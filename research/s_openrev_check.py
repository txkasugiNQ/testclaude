"""Re-measure B1 from the actual decision price (close of the re-cross bar) with per-event RW benchmark."""
from structlib import *
for y in (2023,2024,2025):
    I=[];D=[];ENT=[];AA=[];BB=[];AA_open=[];BB_open=[];ENT_open=[]
    for sd,g in df[rth&(YR==y)].groupby('sd'):
        idx=g.index.values
        if len(idx)<380 or np.isnan(A[idx[0]]): continue
        ro=o[idx[0]]; Aa=A[idx[0]]; hi=-1e9; lo=1e9; armed=0
        for t in idx:
            if m[t]>630: break
            hi=max(hi,h[t]); lo=min(lo,l[t])
            if armed==0:
                if hi-ro>=0.15*Aa: armed=1
                elif ro-lo>=0.15*Aa: armed=-1
            elif (armed==1 and c[t]<ro) or (armed==-1 and c[t]>ro):
                d=-armed; E=hi if armed==1 else lo; exc=abs(E-ro); tgt=ro+d*0.5*exc
                I.append(t); D.append(d); ENT.append(c[t]); AA.append(abs(tgt-c[t])); BB.append(abs(E-c[t]))
                ENT_open.append(ro); AA_open.append(0.5*exc); BB_open.append(exc)
                break
    I=np.array(I,np.int64); D=np.array(D,float)
    for lab,ent,a,b in (('reference = OPEN (as in the descriptive study)',np.array(ENT_open),np.array(AA_open),np.array(BB_open)),
                        ('reference = CLOSE of re-cross bar (real decision)',np.array(ENT),np.array(AA),np.array(BB))):
        ok=a>0; r,_,_=first_hit(h,l,I[ok],D[ok],ent[ok],a[ok],b[ok],flat); dec=r!=0
        print(f"{y} {lab:50s}: P={np.mean(r[dec]>0):.3f}  RW={np.mean((b[ok]/(a[ok]+b[ok]))[dec]):.3f}  N={dec.sum()}")
