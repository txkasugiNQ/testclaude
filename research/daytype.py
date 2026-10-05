from lab import *
m = B(1); L = daylevels(m)
df = pd.DataFrame(dict(day=m.day, tod=m.tod, c=m.c, h=m.h, l=m.l, vw=m.vw, sp=m.split))
rows=[]
for d, x in df.groupby('day'):
    if x.sp.iloc[0]=='OOS': continue
    am = x[(x.tod>570)&(x.tod<=720)]; pm = x[(x.tod>720)&(x.tod<=960)]; on = x[x.tod<=570]
    if len(pm)<200 or len(am)<100: continue
    pmr = pm.h.max()-pm.l.min(); amr = am.h.max()-am.l.min()
    pm_eff = abs(pm.c.iloc[-1]-pm.c.iloc[0])/pmr
    am_eff = abs(am.c.iloc[-1]-am.c.iloc[0])/amr
    pm_path = pm.c.diff().abs().sum(); am_path = am.c.diff().abs().sum()
    vwx_am = (np.sign(am.c-am.vw).diff().abs()>0).sum()
    rows.append(dict(sp=x.sp.iloc[0], pm_eff=pm_eff, am_eff=am_eff, pm_er=abs(pm.c.iloc[-1]-pm.c.iloc[0])/pm_path,
                     am_er=abs(am.c.iloc[-1]-am.c.iloc[0])/am_path, amr=amr, pmr=pmr, onr=on.h.max()-on.l.min(),
                     vwx_am=vwx_am, z12=(am.c.iloc[-1]-am.vw.iloc[-1])/amr, amdir=np.sign(am.c.iloc[-1]-am.c.iloc[0]),
                     pmdir=np.sign(pm.c.iloc[-1]-pm.c.iloc[0]), pmmove=pm.c.iloc[-1]-pm.c.iloc[0]))
D = pd.DataFrame(rows)
print(D.groupby('sp')[['pm_eff','pm_er','am_er']].mean())
for f in ['am_eff','am_er','amr','onr','vwx_am','z12']:
    for s in ['IS','VAL']:
        x = D[D.sp==s]
        print(f, s, 'corr with pm_er: %.3f' % np.corrcoef(x[f].abs() if f=='z12' else x[f], x.pm_er)[0,1],
              ' | corr with pm_eff: %.3f' % np.corrcoef(x[f].abs() if f=='z12' else x[f], x.pm_eff)[0,1])
