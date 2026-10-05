from lab import *
from fp import first_passage
b = B(2); m = b.m; L = daylevels(b)
pm = (b.tod >= 720) & (b.tod < 950)
c, o, h, l, v, atr = b.c, b.o, b.h, b.l, b.v, b.atr
S = pd.Series
def lag(x, n): return S(x).groupby(b.day).shift(n).values
def rsum(x, n): return S(x).groupby(b.day).transform(lambda s: s.rolling(n, min_periods=1).sum()).values
def rmax(x, n): return S(x).groupby(b.day).transform(lambda s: s.rolling(n, min_periods=1).max()).values
def rmin(x, n): return S(x).groupby(b.day).transform(lambda s: s.rolling(n, min_periods=1).min()).values
F = {}
d5 = np.sign(c - lag(c,5)); F['dir'] = d5
F['absret5'] = abs(c - lag(c,5))/atr
F['absret15_aligned'] = (c - lag(c,15))/atr * d5
F['rvol1'] = (S(v)/S(v).groupby(b.tod).transform(lambda s: s.shift(1).rolling(20, min_periods=5).mean())).values
F['rvol5'] = rsum(F['rvol1'], 5)/5
sv = v*np.sign(c-o)
F['vimb5'] = rsum(sv,5)/rsum(v,5)*d5
F['zvw_al'] = (c - b.vw)/atr*d5
F['newext'] = np.where(d5>0, (c >= L['rh']-0.01*atr), (c <= L['rl']+0.01*atr)).astype(float)
F['comp_pre'] = lag((rmax(h,20)-rmin(l,20))/atr, 5)
rng = h-l
F['clv_al'] = np.where(rng>0, ((c-l)/np.where(rng>0,rng,1)-0.5)*2, 0)*d5
F['body_al'] = (c-o)/atr*d5
F['tod'] = b.tod
am_eff = (pd.Series(b.tdate).map(b.days.am_close) - pd.Series(b.tdate).map(b.days.rth_open)).values
am_rng = (pd.Series(b.tdate).map(b.days.amh) - pd.Series(b.tdate).map(b.days.aml)).values
F['am_trend_al'] = np.where(b.tod>720, am_eff/am_rng*d5, np.nan)
# round numbers: distance to next 100 level ahead in direction, and distance since crossed behind
r100 = 100.0
ahead = np.where(d5>0, np.ceil(c/r100)*r100 - c, c - np.floor(c/r100)*r100)
F['rn_ahead'] = ahead/atr
F['rn_ahead_pts'] = ahead
F['atr'] = atr
F = pd.DataFrame(F)
idx = np.where(pm & (b.split != 'OOS') & (d5 != 0))[0]
st1 = b.map1[idx].astype(np.int64)
for mult in [1.0, 2.0]:
    up = mult*atr[idx]
    lo, so, mfe, mae = first_passage(m.h, m.l, m.c, m.tod, m.day, st1, up, up, 960)
    cont = np.where(d5[idx]>0, lo, so)
    F.loc[idx, f'C{mult}'] = cont
F['split'] = b.split
F = F.loc[idx]
F.to_pickle('scan3.pkl')
for mult in ['1.0','2.0']:
    print('=== mult', mult, 'baseline cont-first', (F[f'C{mult}']==1).mean(), 'rev-first', (F[f'C{mult}']==-1).mean())
    for f in [x for x in F.columns if x not in ('split','C1.0','C2.0','dir')]:
        x = F[f].replace([np.inf,-np.inf], np.nan)
        q = pd.qcut(x.rank(method='first'), 10, labels=False)
        line=[]
        for sp in ['IS','VAL']:
            mm = F.split==sp
            y = F.loc[mm, f'C{mult}']
            r = (y==1).groupby(q[mm]).mean() / ((y!=0).groupby(q[mm]).mean())
            line.append(' '.join(f'{v:.2f}' for v in r))
        print(f'{f:16s} IS {line[0]} | VAL {line[1]}')
