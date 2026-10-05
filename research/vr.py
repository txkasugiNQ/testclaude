from lab import *
m = B(1)
c = m.c; tod = m.tod; day = m.day; sp = m.split
def vr(mask_fn, label):
    out = {}
    for s in ['IS','VAL']:
        res = []
        for q in [2,5,10,15,30,60]:
            # non-overlapping q-min returns within PM window 12:00-16:00
            sel = (tod > 720) & (tod <= 960) & (sp == s)
            r1 = []
            rq = []
            df = pd.DataFrame(dict(c=c[sel], day=day[sel], tod=tod[sel]))
            df['r'] = df.groupby('day').c.diff()
            v1 = df.r.var()
            df['bk'] = (df.tod - 721)//q
            g = df.groupby(['day','bk']).r.sum(min_count=q)
            res.append(g.var()/(q*v1))
        out[s] = res
    print(label, {k: ' '.join(f'{x:.3f}' for x in v) for k,v in out.items()})
vr(None, 'VR q=2,5,10,15,30,60 PM')
