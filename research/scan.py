from lab import *
from fp import first_passage
b = B(2); m = b.m; L = daylevels(b)
X = b.df.copy()
X['atr'] = b.atr
pm = (b.tod >= 720) & (b.tod < 958)
c = b.c; atr = b.atr
S = pd.Series
def roll_max(x, n): return S(x).groupby(b.day).transform(lambda s: s.rolling(n, min_periods=1).max()).values
def roll_min(x, n): return S(x).groupby(b.day).transform(lambda s: s.rolling(n, min_periods=1).min()).values
def lag(x, n): return S(x).groupby(b.day).shift(n).values
F = {}
F['tod'] = b.tod
F['z_vwap'] = (c - b.vw)/atr
F['vwap_slope15'] = (b.vw - lag(b.vw, 15))/atr
F['pos_rth'] = (c - L['rl'])/(L['rh'] - L['rl'])
F['ret5'] = (c - lag(c,5))/atr; F['ret15'] = (c - lag(c,15))/atr; F['ret30'] = (c - lag(c,30))/atr
F['comp10'] = (roll_max(b.h,10) - roll_min(b.l,10))/atr
F['comp20'] = (roll_max(b.h,20) - roll_min(b.l,20))/atr
F['brk_hi20'] = (c - lag(roll_max(b.h,20),1))/atr
F['brk_lo20'] = (c - lag(roll_min(b.l,20),1))/atr
rng = b.h - b.l
F['bar_rng'] = rng/atr
F['bar_clv'] = np.where(rng>0, (c - b.l)/np.where(rng>0,rng,1), 0.5)
F['bar_body'] = (c - b.o)/atr
F['d_amh'] = (c - L['amh'])/atr; F['d_aml'] = (c - L['aml'])/atr
F['d_onh'] = (c - L['onh'])/atr; F['d_onl'] = (c - L['onl'])/atr
F['dayrng_atr'] = (L['rh'] - L['rl'])/atr
F['pm_pos'] = (c - L['pl'])/(L['ph'] - L['pl'] + 1e-9)
F['atr'] = atr
F['ret_open'] = (c - L['ro'])/atr
# relative volume vs same-tod average of previous 20 days
vv = S(b.v); key = b.tod
F['rvol'] = (vv / vv.groupby(key).transform(lambda s: s.shift(1).rolling(20, min_periods=5).mean())).values
F = pd.DataFrame(F)
idx = np.where(pm & (b.split != 'OOS'))[0]
st1 = b.map1[idx]
for mult in [1.5, 3.0]:
    up = mult*atr[idx]; dn = mult*atr[idx]
    lo, so, mfe, mae = first_passage(m.h, m.l, m.c, m.tod, m.day, st1.astype(np.int64), up, dn, 960)
    F.loc[idx, f'L{mult}'] = lo; F.loc[idx, f'S{mult}'] = so
F['split'] = b.split
F.to_pickle('scan2.pkl')
print('saved', len(idx))
