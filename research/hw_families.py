import sys, time, pickle
from hw_lab import *
tf = int(sys.argv[1]) if len(sys.argv) > 1 else 2
H = HW(tf); b = H.b; L = H.L
c, o, h, l, atr, day, tod = b.c, b.o, b.h, b.l, b.atr, b.day, b.tod
S = pd.Series
lag = lambda x, n: S(x).groupby(day).shift(n).values
rmax = lambda x, n: S(x).groupby(day).transform(lambda s: s.rolling(n, min_periods=1).max()).values
rmin = lambda x, n: S(x).groupby(day).transform(lambda s: s.rolling(n, min_periods=1).min()).values
win = (tod >= 718) & (tod < 956) & (b.split != 'OOS')          # OOS masked during discovery
def edge(cond):
    prev = S(cond).groupby(day).shift(1).fillna(False).values.astype(bool)
    return cond & ~prev
rr = [0.25, 0.33, 0.5, 0.67, 0.75, 1.0, 1.5]; ss_atr = [0.75, 1.0, 1.5, 2.0]; holds = [5, 10, 20, 40, 10000]
results = {}
def go(name, ev, unit, ss=ss_atr):
    if len(ev) < 80: return
    ev2, R = H.run(ev, unit, rr, ss, holds)
    D = summarize(ev2, R, rr, ss, holds)
    D['family'] = name; D['n_ev'] = len(ev2)
    results[name] = D
t0 = time.time()
# ---------- F1 impulse exhaustion fade ----------
for n in (3, 5, 10):
    imp = (c - lag(c, n)) / atr
    for mth in (2, 3, 4):
        for dirn in (1, -1):
            pass
        cond_up = edge(win & (imp >= mth)); cond_dn = edge(win & (imp <= -mth))
        sig = np.r_[np.where(cond_up)[0], np.where(cond_dn)[0]]; side = np.r_[-np.ones(cond_up.sum(), int), np.ones(cond_dn.sum(), int)]
        o_ = np.argsort(sig); sig, side = sig[o_], side[o_]
        ev = H.market(sig, side)
        go(f'EXH n{n} m{mth} atr', ev, b.atr[ev.sig.values])
        ext = np.where(ev.side.values < 0, rmax(h, n)[ev.sig.values], rmin(l, n)[ev.sig.values])
        u = np.abs(ext - ev.epx.values) + 0.25
        u = np.where((u >= 0.5*b.atr[ev.sig.values]) & (u <= 4*b.atr[ev.sig.values]), u, np.nan)
        go(f'EXH n{n} m{mth} struct', ev, u, ss=[1.0, 1.25])
        # with reversal-candle confirmation: first bar within 3 that closes against impulse
        conf_sig = []; conf_side = []
        cu = np.where(cond_up)[0]; cd = np.where(cond_dn)[0]
        for arr, sd in ((cu, -1), (cd, 1)):
            for i in arr:
                for j in range(i, min(i + 4, len(c))):
                    if day[j] != day[i]: break
                    if (sd < 0 and c[j] < o[j]) or (sd > 0 and c[j] > o[j]):
                        conf_sig.append(j); conf_side.append(sd); break
        if conf_sig:
            cs = np.array(conf_sig); cside = np.array(conf_side); o_ = np.argsort(cs)
            ev = H.market(cs[o_], cside[o_])
            go(f'EXH n{n} m{mth} conf atr', ev, b.atr[ev.sig.values])
print('F1', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F2 consecutive bars ----------
up = (c > lag(c, 1)).astype(float); dn = (c < lag(c, 1)).astype(float)
for k in (4, 5, 6):
    ru = S(up).groupby(day).transform(lambda s: s.rolling(k, min_periods=k).sum()).values
    rd = S(dn).groupby(day).transform(lambda s: s.rolling(k, min_periods=k).sum()).values
    mv = (c - lag(c, k)) / atr
    cu = edge(win & (ru == k) & (mv >= 2)); cd = edge(win & (rd == k) & (mv <= -2))
    sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[-np.ones(cu.sum(), int), np.ones(cd.sum(), int)]
    o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_]); go(f'CONS k{k}', ev, b.atr[ev.sig.values])
print('F2', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F3 VWAP band ----------
vw, sd_ = L['vw'], L['vsd']
for k in (2.0, 2.5, 3.0):
    upb, dnb = vw + k*sd_, vw - k*sd_
    tu = edge(win & (h >= upb)); td_ = edge(win & (l <= dnb))
    for mode in ('touch', 'reject'):
        if mode == 'touch': cu, cd = tu, td_
        else: cu, cd = tu & (c < upb), td_ & (c > dnb)
        sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[-np.ones(cu.sum(), int), np.ones(cd.sum(), int)]
        o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_]); go(f'VWB {k}sd {mode}', ev, b.atr[ev.sig.values])
        # structural: stop beyond bar extreme
        ext = np.where(ev.side.values < 0, h[ev.sig.values], l[ev.sig.values])
        u = np.abs(ext - ev.epx.values) + 0.25; u = np.where((u >= 0.5*b.atr[ev.sig.values]) & (u <= 4*b.atr[ev.sig.values]), u, np.nan)
        go(f'VWB {k}sd {mode} struct', ev, u, ss=[1.0, 1.25])
print('F3', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F4 range extension fade ----------
for up_name, dn_name in (('amh','aml'), ('ibh','ibl'), ('onh','onl'), ('pdh','pdl')):
    for d in (0.5, 1.0, 2.0):
        cu = edge(win & ((c - L[up_name]) >= d*atr)); cd = edge(win & ((L[dn_name] - c) >= d*atr))
        sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[-np.ones(cu.sum(), int), np.ones(cd.sum(), int)]
        o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_]); go(f'RNG {up_name}/{dn_name} d{d}', ev, b.atr[ev.sig.values])
print('F4', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F5 failed breakout of session extreme ----------
prh = lag(L['rh'], 1); prl = lag(L['rl'], 1)
newhi = win & (h > prh) & (tod > 600); newlo = win & (l < prl) & (tod > 600)
for j in (1, 2, 3):
    sigs = []; sides = []; exts = []
    for arr, sd in ((np.where(newhi)[0], -1), (np.where(newlo)[0], 1)):
        for i in arr:
            lvl = prh[i] if sd < 0 else prl[i]
            for k_ in range(i, min(i + j + 1, len(c))):
                if day[k_] != day[i]: break
                if (sd < 0 and c[k_] < lvl) or (sd > 0 and c[k_] > lvl):
                    sigs.append(k_); sides.append(sd); exts.append(L['rh'][k_] if sd < 0 else L['rl'][k_]); break
    sg = np.array(sigs); sdd = np.array(sides); ex = np.array(exts); o_ = np.argsort(sg, kind='stable')
    sg, sdd, ex = sg[o_], sdd[o_], ex[o_]
    keep = np.r_[True, sg[1:] != sg[:-1]]; sg, sdd, ex = sg[keep], sdd[keep], ex[keep]
    ev = H.market(sg, sdd); exm = pd.Series(ex, index=sg).reindex(ev.sig.values).values
    go(f'FBO j{j} atr', ev, b.atr[ev.sig.values])
    u = np.abs(exm - ev.epx.values) + 0.25; u = np.where((u >= 0.5*b.atr[ev.sig.values]) & (u <= 4*b.atr[ev.sig.values]), u, np.nan)
    go(f'FBO j{j} struct', ev, u, ss=[1.0, 1.25])
print('F5', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F6 sweep-reclaim of key levels ----------
for nm, sd in (('amh',-1),('aml',1),('onh',-1),('onl',1),('pdh',-1),('pdl',1),('ibh',-1),('ibl',1)):
    X = L[nm]; pX = lag(X, 1)
    if sd < 0: cond = win & (h > X) & (c < X) & (lag(c, 1) < pX)
    else: cond = win & (l < X) & (c > X) & (lag(c, 1) > pX)
    idx = np.where(cond)[0]
    if len(idx) < 40: continue
    results_side = H.market(idx, np.full(len(idx), sd))
    if nm in ('amh',): ev_all = results_side
    else: ev_all = pd.concat([ev_all, results_side])
ev_all = ev_all.sort_values('ent').reset_index(drop=True)
go('SWP keylevels atr', ev_all, b.atr[ev_all.sig.values])
print('F6', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F7 trend-day pullback (continuation, small target) ----------
ro = L['ro']; adr = H.adr; reg = H.reg
tdu = (reg > 0) & ((c - ro) >= 0.3*adr); tdd = (reg < 0) & ((ro - c) >= 0.3*adr)
for D_ in (1.5, 2.5, 4.0):
    cu = edge(win & tdu & ((L['rh'] - c) >= D_*atr)); cd = edge(win & tdd & ((c - L['rl']) >= D_*atr))
    sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[np.ones(cu.sum(), int), -np.ones(cd.sum(), int)]
    o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_]); go(f'TDPB D{D_}', ev, b.atr[ev.sig.values])
print('F7', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F8 range-day new extreme fade ----------
rday = np.abs(c - ro) < 0.25*adr
for minbars in (0,):
    cu = win & rday & (h > prh); cd = win & rday & (l < prl)
    sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[-np.ones(cu.sum(), int), np.ones(cd.sum(), int)]
    o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_]); go('RDAY newext fade', ev, b.atr[ev.sig.values])
    ext = np.where(ev.side.values < 0, h[ev.sig.values], l[ev.sig.values])
    u = np.abs(ext - ev.epx.values) + 0.25; u = np.where((u >= 0.5*b.atr[ev.sig.values]) & (u <= 4*b.atr[ev.sig.values]), u, np.nan)
    go('RDAY newext fade struct', ev, u, ss=[1.0, 1.25])
# all new extremes (any day) fade
cu = win & (h > prh) & (tod > 600); cd = win & (l < prl) & (tod > 600)
sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[-np.ones(cu.sum(), int), np.ones(cd.sum(), int)]
o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_]); go('ALLDAY newext fade', ev, b.atr[ev.sig.values])
print('F8', f'{time.time()-t0:.0f}s', flush=True)
# ---------- F9 bar-spike fade (single bar range >= k ATR, close near extreme) ----------
rng = h - l; clv = np.where(rng > 0, (c - l)/np.where(rng > 0, rng, 1), 0.5)
for k in (2.0, 3.0):
    cu = win & (rng >= k*lag(atr, 1)) & (clv > 0.7) & (c > o); cd = win & (rng >= k*lag(atr, 1)) & (clv < 0.3) & (c < o)
    sig = np.r_[np.where(cu)[0], np.where(cd)[0]]; side = np.r_[-np.ones(cu.sum(), int), np.ones(cd.sum(), int)]
    o_ = np.argsort(sig); ev = H.market(sig[o_], side[o_]); go(f'SPIKE k{k} fade', ev, b.atr[ev.sig.values])
    ev2 = H.market(sig[o_], -side[o_]); go(f'SPIKE k{k} follow', ev2, b.atr[ev2.sig.values])
print('F9', f'{time.time()-t0:.0f}s', flush=True)
pickle.dump(results, open(f'hw_results_tf{tf}.pkl', 'wb'))
A = pd.concat(results.values(), ignore_index=True)
A.to_pickle(f'hw_all_tf{tf}.pkl')
print('families', len(results), 'cells', len(A))
