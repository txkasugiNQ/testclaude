from wf import *
import json
tr=pd.read_pickle('tr_F14_impulse_retrace_limit.pkl')
O,sel=wf_select(tr,2)
for s in sel: print(s)
# predefined protocol on 2023 only: max WR23 subject to TPD23>=2
d23=df[df.sd<'2024-01-01'].sd.nunique(); d2425=df[df.sd>='2024-01-01'].sd.nunique()
best=None
for k,T in tr.items():
    a=T[T.sd<'2024-01-01']
    if len(a)/d23<2: continue
    sc=(round(a.win.mean(),3),a.pnlR.mean())
    if best is None or sc>best[0]: best=(sc,k)
print("\nFROZEN (chosen on 2023 only):",best)
T=tr[best[1]]; b=T[T.sd>='2024-01-01']; print("2023:",stats(T[T.sd<'2024-01-01'],d23)); print("2024-25 OOS:",stats(b,d2425))
