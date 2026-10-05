from ldn_lab import *
m = LB(1); L = m.L
df = pd.DataFrame(dict(day=m.day, t=m.ltod, o=m.o, h=m.h, l=m.l, c=m.c, sp=m.split, atr=m.atr,
                       asiah=L['asiah'], asial=L['asial'], frah=L['frah'], fral=L['fral'], pdh=L['pdh'], pdl=L['pdl']))
df = df[df.sp != 'OOS']
lon = df[(df.t > 480) & (df.t <= 720)]
rows = []
for d, x in lon.groupby('day'):
    if len(x) < 220: continue
    ih = x.h.values.argmax(); il = x.l.values.argmin()
    o0 = x.o.iloc[0]; c30 = x.c.values[29]; c60 = x.c.values[59]; cend = x.c.iloc[-1]
    rows.append(dict(day=d, sp=x.sp.iloc[0], th=x.t.values[ih] - 480, tl=x.t.values[il] - 480,
                     r30=c30 - o0, r30_rest=cend - c30, r60=c60 - o0, r60_rest=cend - c60, rng=x.h.max() - x.l.min(),
                     hi_first=ih < il,
                     sw_ah=(x.h > x.asiah).any(), sw_al=(x.l < x.asial).any(), sw_fh=(x.h > x.frah).any(), sw_fl=(x.l < x.fral).any()))
D = pd.DataFrame(rows)
print('days', len(D), D.groupby('sp').size().to_dict())
for f, lab in ((30, 'first 30 min'), (60, 'first 60 min'), (15, 'first 15 min')):
    rw = 2/np.pi*np.arcsin(np.sqrt(f/240))
    for sp in ('IS', 'VAL'):
        q = D[D.sp == sp]
        p_h = (q.th <= f).mean(); p_l = (q.tl <= f).mean(); p_any = ((q.th <= f) | (q.tl <= f)).mean()
        print(f'{lab:13s} {sp}: P(London HIGH set) {p_h:.2f}  P(LOW set) {p_l:.2f}  P(either) {p_any:.2f}   | random-walk each {rw:.2f}, either ~{1-(1-rw)**2:.2f}(indep. approx)')
# end-of-window clustering too (random walk is symmetric: last f minutes has same probability)
for sp in ('IS','VAL'):
    q = D[D.sp == sp]
    print(f'{sp}: P(HIGH in last 30 min) {(q.th > 210).mean():.2f}  P(LOW in last 30) {(q.tl > 210).mean():.2f}')
print()
for a, bcol, lab in (('r30','r30_rest','first 30m vs rest'), ('r60','r60_rest','first 60m vs rest')):
    for sp in ('IS','VAL'):
        q = D[D.sp == sp]
        print(f'{lab} {sp}: corr={np.corrcoef(q[a], q[bcol])[0,1]:+.3f}  P(opposite sign)={(np.sign(q[a]) != np.sign(q[bcol])).mean():.3f}')
print()
for k in ('sw_ah','sw_al','sw_fh','sw_fl'):
    print(k, D.groupby('sp')[k].mean().round(3).to_dict())
D.to_pickle('ldn_days.pkl')
