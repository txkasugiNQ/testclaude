"""Bar-exact Python/numba replica of the Pine indicator "NQ Structure Levels" (ScriptTest).

Everything is evaluated on CLOSED bars in the same order as the Pine script:
  1) interactions with existing levels  2) new-level detection  3) scoring + pruning
A level created on bar i is therefore first evaluated for interactions on bar i+1.

Research extensions (NOT part of the indicator, clearly separated):
  * pool 1 = key levels (PDH/PDL/PDC/PWH/PWL/ONH/ONL/LDNH/LDNL/pRTHH/pRTHL/ORH/ORL) tracked as their own
    level objects with the indicator's touch/reject/sweep/break/retest logic (the indicator itself only
    uses them as a confluence count).
  * pool 2 = placebo "shadow" levels at +/- SHADOW_ATR * ATR around each newly created structural level,
    living as long as their parent. They use the identical interaction logic and serve as control group.

Every event is logged with a snapshot of the level state BEFORE the bar's interaction (no lookahead).
"""
import numpy as np, pandas as pd
from numba import njit

TICK = 0.25

# ---------------------------------------------------------------- default inputs (= Pine defaults)
P = dict(atrLen=21, histDays=5, maxLevels=50, decay=0.85, tolATR=0.25, eqFactor=0.5, touchFactor=0.5,
         breakATR=0.15, swLen=5, majLen=15, minProm=1.0, minLeg=1.5, majProm=3.0, minBars=5, dispATR=1.5,
         volMult=1.5, volLen=20, rangeLen=30, rangeMin=40, rangeATR=3.0, rangeTests=2, rejATR=0.3,
         touchCool=3, fakeBars=6, retestMove=0.75, retestMax=60, htfLen=3,
         tf5=True, tf15=True, tf30=False, tf60=True, tf240=True, tfD=True)
SHADOW_ATR = 1.0

# ---------------------------------------------------------------- helpers (TradingView semantics)

def rma(x, n):
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = np.nanmean(x[:n])
    a = 1.0 / n
    for i in range(n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def atr(h, l, c, n):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    tr[0] = h[0] - l[0]
    return rma(tr, n)


@njit(cache=True)
def pivots(src, left, right, high):
    """Value at the CONFIRMATION bar (center + right), NaN otherwise.
    Tie rule (conservative, to be verified vs TV): center must be >= all left bars and > all right bars
    for highs (mirror for lows) -> with equal extremes the RIGHT-most bar is the pivot (latest confirmation)."""
    n = len(src)
    out = np.full(n, np.nan)
    for i in range(left + right, n):
        cidx = i - right
        v = src[cidx]
        ok = True
        for k in range(1, left + 1):
            w = src[cidx - k]
            if (high and w > v) or ((not high) and w < v):
                ok = False
                break
        if ok:
            for k in range(1, right + 1):
                w = src[cidx + k]
                if (high and w >= v) or ((not high) and w <= v):
                    ok = False
                    break
        if ok:
            out[i] = v
    return out


def roll_max(x, n):
    return pd.Series(x).rolling(n, min_periods=n).max().values


def roll_min(x, n):
    return pd.Series(x).rolling(n, min_periods=n).min().values


# ---------------------------------------------------------------- bar construction

def make_bars(df1, tf):
    """Aggregate 1m (open-time stamped) to tf minutes, aligned to the 18:00 ET session open."""
    if tf == 1:
        b = df1[["t", "open", "high", "low", "close", "volume", "tday"]].copy()
    else:
        sess0 = df1["tday"] - pd.Timedelta(hours=6)   # 18:00 ET of the session open
        k = ((df1["t"] - sess0).dt.total_seconds() // (60 * tf)).astype(np.int64)
        tstart = sess0 + pd.to_timedelta(k * tf, unit="m")
        g = pd.DataFrame({"key": tstart.values, "open": df1["open"].values, "high": df1["high"].values,
                          "low": df1["low"].values, "close": df1["close"].values,
                          "volume": df1["volume"].values, "tday": df1["tday"].values}).groupby("key", sort=True)
        b = pd.DataFrame({"t": g.size().index.values, "open": g["open"].first().values,
                          "high": g["high"].max().values, "low": g["low"].min().values,
                          "close": g["close"].last().values, "volume": g["volume"].sum().values,
                          "tday": g["tday"].first().values})
    b = b.reset_index(drop=True)
    b["mod"] = b["t"].dt.hour * 60 + b["t"].dt.minute
    return b


def htf_index(b, tfmin):
    """Index of the higher-timeframe bar each chart bar belongs to (TV alignment assumption:
    5/15/30/60 clock aligned, 240 and D anchored at the 18:00 ET session open)."""
    if tfmin == "D":
        return pd.factorize(b["tday"])[0]
    sess0 = b["tday"] - pd.Timedelta(hours=6)
    if tfmin == 240:
        k = ((b["t"] - sess0).dt.total_seconds() // (60 * 240)).astype(np.int64)
        key = b["tday"].values.astype("datetime64[m]").astype(np.int64) * 100 + k.values
    else:
        key = b["t"].dt.floor(f"{tfmin}min").values.astype(np.int64)
    return pd.factorize(key)[0]


def htf_pivots(b, tfmin, plen):
    """Returns per chart bar: nb (first chart bar of a new HTF bar) and the HTF pivot high/low value that
    request.security(tf, [ph[1], pl[1]], lookahead_on) delivers there = pivot confirmed by the HTF bar that
    just CLOSED (no lookahead)."""
    k = htf_index(b, tfmin)
    g = pd.DataFrame({"k": k, "h": b["high"].values, "l": b["low"].values}).groupby("k")
    H = g["h"].max().values
    L = g["l"].min().values
    ph = pivots(H, plen, plen, True)
    pl = pivots(L, plen, plen, False)
    nb = np.r_[False, k[1:] != k[:-1]]
    prev = k - 1
    vh = np.where(prev >= 0, ph[np.clip(prev, 0, None)], np.nan)
    vl = np.where(prev >= 0, pl[np.clip(prev, 0, None)], np.nan)
    return nb, vh, vl


def session_tracker(inS, h, l):
    """f_sess(): last COMPLETED session high/low (+developing)."""
    n = len(h)
    lastH = np.full(n, np.nan); lastL = np.full(n, np.nan)
    curH = np.full(n, np.nan); curL = np.full(n, np.nan)
    cH = np.nan; cL = np.nan; LH = np.nan; LL = np.nan; was = False
    for i in range(n):
        s = inS[i]
        if s and not was:
            cH = h[i]; cL = l[i]
        elif s:
            cH = max(cH, h[i]); cL = min(cL, l[i])
        if (not s) and was:
            LH = cH; LL = cL
        lastH[i] = LH; lastL[i] = LL; curH[i] = cH; curL[i] = cL
        was = s
    return lastH, lastL, curH, curL


def precompute(b, p=P):
    o = b["open"].values.astype(np.float64); h = b["high"].values.astype(np.float64)
    l = b["low"].values.astype(np.float64); c = b["close"].values.astype(np.float64)
    v = b["volume"].values.astype(np.float64)
    n = len(b)
    A = atr(h, l, c, p["atrLen"])
    mergeTol = np.maximum(np.nan_to_num(A * p["tolATR"]), 2 * TICK)
    eqTol = np.maximum(mergeTol * p["eqFactor"], TICK)
    touchTol = np.maximum(mergeTol * p["touchFactor"], TICK)
    breakBuf = np.maximum(p["breakATR"] * np.nan_to_num(A), TICK)
    # trading day / week
    tday = b["tday"].values
    newDay = np.r_[False, tday[1:] != tday[:-1]]
    wk = pd.to_datetime(b["tday"]).dt.to_period("W-SUN").astype(np.int64).values  # Mon..Sun weeks
    newWeek = np.r_[False, wk[1:] != wk[:-1]]
    dayIndex = np.cumsum(newDay)
    # VWAP anchored at the session (day) start, hlc3
    hlc3 = (h + l + c) / 3
    gid = dayIndex
    pv = pd.Series(hlc3 * v).groupby(gid).cumsum().values
    vv = pd.Series(v).groupby(gid).cumsum().values
    vwap = np.where(vv > 0, pv / np.where(vv > 0, vv, 1), np.nan)
    volAvg = np.nan_to_num(pd.Series(v).rolling(p["volLen"], min_periods=p["volLen"]).mean().values)
    winVol = roll_max(v, 2 * p["swLen"] + 1)
    mWinVol = roll_max(v, 2 * p["majLen"] + 1)
    volSw = (volAvg > 0) & (np.nan_to_num(winVol) >= volAvg * p["volMult"])
    volMaj = (volAvg > 0) & (np.nan_to_num(mWinVol) >= volAvg * p["volMult"])
    # previous day / week
    pdh = np.full(n, np.nan); pdl = np.full(n, np.nan); pdc = np.full(n, np.nan)
    pwh = np.full(n, np.nan); pwl = np.full(n, np.nan)
    dH = np.nan; dL = np.nan; wH = np.nan; wL = np.nan; a = b_ = cc = np.nan; ww1 = ww2 = np.nan
    dcount = 0; wcount = 0
    for i in range(n):
        if newDay[i]:
            if dcount > 0:
                a, b_, cc = dH, dL, c[i - 1]
            dcount += 1; dH = h[i]; dL = l[i]
        else:
            dH = h[i] if np.isnan(dH) else max(dH, h[i]); dL = l[i] if np.isnan(dL) else min(dL, l[i])
        if newWeek[i]:
            if wcount > 0:
                ww1, ww2 = wH, wL
            wcount += 1; wH = h[i]; wL = l[i]
        else:
            wH = h[i] if np.isnan(wH) else max(wH, h[i]); wL = l[i] if np.isnan(wL) else min(wL, l[i])
        pdh[i], pdl[i], pdc[i], pwh[i], pwl[i] = a, b_, cc, ww1, ww2
    mod = b["mod"].values
    inON = (mod >= 1080) | (mod < 570)
    inLN = (mod >= 180) & (mod < 480)
    inRT = (mod >= 570) & (mod < 960)
    inOR = (mod >= 570) & (mod < 585)
    onH, onL, _, _ = session_tracker(inON, h, l)
    lnH, lnL, _, _ = session_tracker(inLN, h, l)
    rtH, rtL, _, _ = session_tracker(inRT, h, l)
    orH, orL, _, _ = session_tracker(inOR, h, l)
    # OR session start time of last completed OR must be >= start of current day
    orStartDay = np.full(n, -1); cur = -1; last = -1; was = False
    for i in range(n):
        if inOR[i] and not was:
            cur = dayIndex[i]
        if (not inOR[i]) and was:
            last = cur
        orStartDay[i] = last; was = inOR[i]
    orToday = (orStartDay >= 0) & (orStartDay == dayIndex) & (dayIndex > 0)
    orH = np.where(orToday, orH, np.nan); orL = np.where(orToday, orL, np.nan)
    keys = np.c_[pdh, pdl, pdc, pwh, pwl, onH, onL, lnH, lnL, rtH, rtL, orH, orL]
    # refVersion (Pine: weighted sum of the refP list incl. NaN->0; OR only pushed when orToday)
    w = np.arange(1, 12)
    rs = (np.nan_to_num(keys[:, :11]) * w).sum(1) + np.where(orToday, np.nan_to_num(orH) * 12 + np.nan_to_num(orL) * 13, 0)
    refVersion = np.cumsum(np.r_[True, rs[1:] != rs[:-1]]).astype(np.int64)
    # swings
    sl, ml = p["swLen"], p["majLen"]
    ph = pivots(h, sl, sl, True); pl = pivots(l, sl, sl, False)
    mph = pivots(h, ml, ml, True); mpl = pivots(l, ml, ml, False)
    winLo = roll_min(l, 2 * sl + 1); winHi = roll_max(h, 2 * sl + 1)
    aftLo = roll_min(l, sl); aftHi = roll_max(h, sl)
    mWinLo = roll_min(l, 2 * ml + 1); mWinHi = roll_max(h, 2 * ml + 1)
    mAftLo = roll_min(l, ml); mAftHi = roll_max(h, ml)
    rwHi = roll_max(h, p["rangeLen"]); rwLo = roll_min(l, p["rangeLen"])
    # HTF pivots
    chart_min = int(round((b["t"].diff().dt.total_seconds().median()) / 60))
    tfs = [(5, p["tf5"], 0.5, 1), (15, p["tf15"], 0.75, 2), (30, p["tf30"], 1.0, 4),
           (60, p["tf60"], 1.25, 8), (240, p["tf240"], 1.5, 16), ("D", p["tfD"], 2.0, 32)]
    HN = len(tfs)
    htf_nb = np.zeros((n, HN), np.bool_); htf_h = np.full((n, HN), np.nan); htf_l = np.full((n, HN), np.nan)
    htf_w = np.zeros(HN); htf_bit = np.zeros(HN, np.int64); htf_on = np.zeros(HN, np.bool_)
    for j, (tfm, on, wgt, bit) in enumerate(tfs):
        okTF = (tfm == "D") or (tfm > chart_min)
        htf_w[j] = wgt; htf_bit[j] = bit; htf_on[j] = on and okTF
        if htf_on[j]:
            nb, vh, vl = htf_pivots(b, tfm, p["htfLen"])
            htf_nb[:, j] = nb; htf_h[:, j] = vh; htf_l[:, j] = vl
    return dict(o=o, h=h, l=l, c=c, v=v, atr=A, mergeTol=mergeTol, eqTol=eqTol, touchTol=touchTol,
                breakBuf=breakBuf, dayIndex=dayIndex.astype(np.int64), vwap=vwap, volSw=volSw, volMaj=volMaj,
                keys=keys, refVersion=refVersion, ph=ph, pl=pl, mph=mph, mpl=mpl, winLo=winLo, winHi=winHi,
                aftLo=aftLo, aftHi=aftHi, mWinLo=mWinLo, mWinHi=mWinHi, mAftLo=mAftLo, mAftHi=mAftHi,
                rwHi=rwHi, rwLo=rwLo, htf_nb=htf_nb, htf_h=htf_h, htf_l=htf_l, htf_w=htf_w, htf_bit=htf_bit,
                htf_on=htf_on, mod=b["mod"].values.astype(np.int64))


# ---------------------------------------------------------------- level pool layout
# float fields
F_PRICE, F_TOP, F_BOT, F_MTF, F_CONF, F_STR = range(6)
NF = 6
# int fields
(I_UID, I_BORNDAY, I_CREATED, I_LASTREACT, I_DIR, I_SIDE, I_LASTSW, I_SWHITS, I_MAJOR, I_RANGEHITS, I_EQHITS,
 I_MTFMASK, I_VOLHIT, I_DISPHIT, I_TOUCHES, I_REJ, I_BRK, I_RET, I_FAKE, I_LASTTOUCH, I_INTOUCH, I_REJDONE,
 I_SWEEPDONE, I_BRKDIR, I_BRKBAR, I_BRKMOVED, I_REFCOUNT, I_REFVER, I_NEARVWAP, I_RANK, I_EVERHC, I_KIND,
 I_PARENT, I_KEYTYPE, I_DEAD) = range(35)
NI = 35
CAP = 200
# kind bitmask: 1 swing, 2 major, 4 range, 8 htf, 16 key, 32 shadow

EV_TOUCH, EV_REJECT, EV_SWEEP, EV_BREAK, EV_FAKE, EV_RETEST, EV_CREATE, EV_REMOVE, EV_MERGE = range(1, 10)
# event record columns (float matrix)
EVCOLS = ["bar", "uid", "pool", "etype", "edir", "price", "top", "bot", "side", "strength", "conf", "rank",
          "touches", "rej", "brk", "ret", "fake", "swhits", "major", "rangehits", "eqhits", "mtf", "mtfmask",
          "refcount", "nearvwap", "volhit", "disphit", "created", "bornday", "lastreact", "day", "dirformed",
          "kind", "keytype", "parent", "n_s05", "n_s10", "n_s20", "n_k05", "n_k10", "n_k20", "d_s", "d_k",
          "atr", "x1", "x2"]
NE = len(EVCOLS)


@njit(cache=True)
def _emit(EV, ne, i, pool, pidx, F, I, et, edir, day, atr_i, SF, SI, sn, KF, kn, x1, x2, snapF, snapI):
    if ne >= EV.shape[0]:
        return ne
    r = EV[ne]
    r[0] = i; r[1] = snapI[I_UID]; r[2] = pool; r[3] = et; r[4] = edir
    r[5] = snapF[F_PRICE]; r[6] = snapF[F_TOP]; r[7] = snapF[F_BOT]; r[8] = snapI[I_SIDE]
    r[9] = snapF[F_STR]; r[10] = snapF[F_CONF]; r[11] = snapI[I_RANK]
    r[12] = snapI[I_TOUCHES]; r[13] = snapI[I_REJ]; r[14] = snapI[I_BRK]; r[15] = snapI[I_RET]; r[16] = snapI[I_FAKE]
    r[17] = snapI[I_SWHITS]; r[18] = snapI[I_MAJOR]; r[19] = snapI[I_RANGEHITS]; r[20] = snapI[I_EQHITS]
    r[21] = snapF[F_MTF]; r[22] = snapI[I_MTFMASK]; r[23] = snapI[I_REFCOUNT]; r[24] = snapI[I_NEARVWAP]
    r[25] = snapI[I_VOLHIT]; r[26] = snapI[I_DISPHIT]; r[27] = snapI[I_CREATED]; r[28] = snapI[I_BORNDAY]
    r[29] = snapI[I_LASTREACT]; r[30] = day; r[31] = snapI[I_DIR]; r[32] = snapI[I_KIND]; r[33] = snapI[I_KEYTYPE]
    r[34] = snapI[I_PARENT]
    pr = snapF[F_PRICE]
    a5 = 0; a10 = 0; a20 = 0; ds = 1e9
    for j in range(sn):
        if pool == 0 and j == pidx:
            continue
        d = abs(SF[j, F_PRICE] - pr)
        if d < ds:
            ds = d
        if d <= 0.5 * atr_i: a5 += 1
        if d <= 1.0 * atr_i: a10 += 1
        if d <= 2.0 * atr_i: a20 += 1
    b5 = 0; b10 = 0; b20 = 0; dk = 1e9
    for j in range(kn):
        if pool == 1 and j == pidx:
            continue
        d = abs(KF[j, F_PRICE] - pr)
        if d < dk:
            dk = d
        if d <= 0.5 * atr_i: b5 += 1
        if d <= 1.0 * atr_i: b10 += 1
        if d <= 2.0 * atr_i: b20 += 1
    r[35] = a5; r[36] = a10; r[37] = a20; r[38] = b5; r[39] = b10; r[40] = b20; r[41] = ds; r[42] = dk
    r[43] = atr_i; r[44] = x1; r[45] = x2
    return ne + 1


@njit(cache=True)
def _interact(i, pool, F, I, n_, h, l, c, atr_i, touchTol, breakBuf, day, p_rej, p_cool, p_fake, p_rmove, p_rmax,
              EV, ne, SF, SI, sn, KF, kn, v2):
    rejDist = p_rej * atr_i
    snapF = np.empty(NF); snapI = np.empty(NI, np.int64)
    for j in range(n_):
        if I[j, I_DEAD] == 1:
            continue
        zt = F[j, F_TOP]; zb = F[j, F_BOT]; price = F[j, F_PRICE]
        for q in range(NF): snapF[q] = F[j, q]
        for q in range(NI): snapI[q] = I[j, q]
        touched = (h >= zb - touchTol) and (l <= zt + touchTol)
        if v2 and I[j, I_BRKDIR] != 0:
            # research v2: a broken level is only followed for false-break / retest, then it dies
            I[j, I_INTOUCH] = 1 if touched else 0
            if i <= I[j, I_BRKBAR]:
                continue
            age = i - I[j, I_BRKBAR]
            bd = I[j, I_BRKDIR]
            if age <= p_fake and ((bd == 1 and c < price) or (bd == -1 and c > price)):
                I[j, I_FAKE] += 1; I[j, I_SIDE] = -bd; I[j, I_BRKDIR] = 0; I[j, I_LASTREACT] = day
                I[j, I_LASTTOUCH] = i
                ne = _emit(EV, ne, i, pool, j, F, I, EV_FAKE, -bd, day, atr_i, SF, SI, sn, KF, kn, age, h if bd == 1 else l, snapF, snapI)
                continue
            if bd == 1:
                if h - zt >= p_rmove * atr_i: I[j, I_BRKMOVED] = 1
                if I[j, I_BRKMOVED] == 1 and l <= zt + touchTol and c > zt:
                    I[j, I_RET] += 1; I[j, I_DEAD] = 1
                    ne = _emit(EV, ne, i, pool, j, F, I, EV_RETEST, 1, day, atr_i, SF, SI, sn, KF, kn, age, l, snapF, snapI)
                elif age > p_rmax or c < zb - breakBuf:
                    I[j, I_DEAD] = 1
            else:
                if zb - l >= p_rmove * atr_i: I[j, I_BRKMOVED] = 1
                if I[j, I_BRKMOVED] == 1 and h >= zb - touchTol and c < zb:
                    I[j, I_RET] += 1; I[j, I_DEAD] = 1
                    ne = _emit(EV, ne, i, pool, j, F, I, EV_RETEST, -1, day, atr_i, SF, SI, sn, KF, kn, age, h, snapF, snapI)
                elif age > p_rmax or c > zt + breakBuf:
                    I[j, I_DEAD] = 1
            continue
        if touched and I[j, I_INTOUCH] == 0 and i - I[j, I_LASTTOUCH] >= p_cool:
            I[j, I_TOUCHES] += 1; I[j, I_LASTTOUCH] = i; I[j, I_LASTREACT] = day
            I[j, I_REJDONE] = 0; I[j, I_SWEEPDONE] = 0
            ne = _emit(EV, ne, i, pool, j, F, I, EV_TOUCH, snapI[I_SIDE], day, atr_i, SF, SI, sn, KF, kn, h, l, snapF, snapI)
        I[j, I_INTOUCH] = 1 if touched else 0
        handled = False
        if I[j, I_BRKDIR] != 0 and i > I[j, I_BRKBAR]:
            age = i - I[j, I_BRKBAR]
            if I[j, I_BRKDIR] == 1:
                if age <= p_fake and c < price:
                    I[j, I_FAKE] += 1; I[j, I_SIDE] = -1; I[j, I_BRKDIR] = 0; I[j, I_LASTREACT] = day; handled = True
                    ne = _emit(EV, ne, i, pool, j, F, I, EV_FAKE, -1, day, atr_i, SF, SI, sn, KF, kn, age, h, snapF, snapI)
                else:
                    if h - zt >= p_rmove * atr_i:
                        I[j, I_BRKMOVED] = 1
                    if I[j, I_BRKMOVED] == 1 and l <= zt + touchTol and c > zt:
                        I[j, I_RET] += 1; I[j, I_BRKDIR] = 0; I[j, I_LASTREACT] = day; handled = True
                        ne = _emit(EV, ne, i, pool, j, F, I, EV_RETEST, 1, day, atr_i, SF, SI, sn, KF, kn, age, l, snapF, snapI)
                    elif age > p_rmax:
                        I[j, I_BRKDIR] = 0
            else:
                if age <= p_fake and c > price:
                    I[j, I_FAKE] += 1; I[j, I_SIDE] = 1; I[j, I_BRKDIR] = 0; I[j, I_LASTREACT] = day; handled = True
                    ne = _emit(EV, ne, i, pool, j, F, I, EV_FAKE, 1, day, atr_i, SF, SI, sn, KF, kn, age, l, snapF, snapI)
                else:
                    if zb - l >= p_rmove * atr_i:
                        I[j, I_BRKMOVED] = 1
                    if I[j, I_BRKMOVED] == 1 and h >= zb - touchTol and c < zb:
                        I[j, I_RET] += 1; I[j, I_BRKDIR] = 0; I[j, I_LASTREACT] = day; handled = True
                        ne = _emit(EV, ne, i, pool, j, F, I, EV_RETEST, -1, day, atr_i, SF, SI, sn, KF, kn, age, h, snapF, snapI)
                    elif age > p_rmax:
                        I[j, I_BRKDIR] = 0
        if not handled:
            if I[j, I_SIDE] == -1 and c > zt + breakBuf:
                I[j, I_SIDE] = 1; I[j, I_BRK] += 1; I[j, I_BRKDIR] = 1; I[j, I_BRKBAR] = i; I[j, I_BRKMOVED] = 0
                ne = _emit(EV, ne, i, pool, j, F, I, EV_BREAK, 1, day, atr_i, SF, SI, sn, KF, kn, h, l, snapF, snapI)
            elif I[j, I_SIDE] == 1 and c < zb - breakBuf:
                I[j, I_SIDE] = -1; I[j, I_BRK] += 1; I[j, I_BRKDIR] = -1; I[j, I_BRKBAR] = i; I[j, I_BRKMOVED] = 0
                ne = _emit(EV, ne, i, pool, j, F, I, EV_BREAK, -1, day, atr_i, SF, SI, sn, KF, kn, h, l, snapF, snapI)
            elif touched:
                if I[j, I_SIDE] == -1:
                    if I[j, I_SWEEPDONE] == 0 and h > zt + breakBuf and c < price:
                        I[j, I_FAKE] += 1; I[j, I_SWEEPDONE] = 1; I[j, I_LASTREACT] = day
                        ne = _emit(EV, ne, i, pool, j, F, I, EV_SWEEP, -1, day, atr_i, SF, SI, sn, KF, kn, h, l, snapF, snapI)
                    if I[j, I_REJDONE] == 0 and c <= zb - rejDist:
                        I[j, I_REJ] += 1; I[j, I_REJDONE] = 1; I[j, I_LASTREACT] = day
                        ne = _emit(EV, ne, i, pool, j, F, I, EV_REJECT, -1, day, atr_i, SF, SI, sn, KF, kn, h, l, snapF, snapI)
                else:
                    if I[j, I_SWEEPDONE] == 0 and l < zb - breakBuf and c > price:
                        I[j, I_FAKE] += 1; I[j, I_SWEEPDONE] = 1; I[j, I_LASTREACT] = day
                        ne = _emit(EV, ne, i, pool, j, F, I, EV_SWEEP, 1, day, atr_i, SF, SI, sn, KF, kn, l, h, snapF, snapI)
                    if I[j, I_REJDONE] == 0 and c >= zt + rejDist:
                        I[j, I_REJ] += 1; I[j, I_REJDONE] = 1; I[j, I_LASTREACT] = day
                        ne = _emit(EV, ne, i, pool, j, F, I, EV_REJECT, 1, day, atr_i, SF, SI, sn, KF, kn, l, h, snapF, snapI)
    return ne


@njit(cache=True)
def _new_slot(F, I, n_, pr, i, day, dirn, c, h, l, touchTol, uid, kind, pivBar):
    F[n_, :] = 0.0; I[n_, :] = 0
    F[n_, F_PRICE] = pr; F[n_, F_TOP] = pr; F[n_, F_BOT] = pr
    I[n_, I_UID] = uid; I[n_, I_BORNDAY] = day; I[n_, I_CREATED] = i; I[n_, I_LASTREACT] = day
    I[n_, I_DIR] = dirn; I[n_, I_SIDE] = 1 if c >= pr else -1
    I[n_, I_LASTSW] = pivBar if pivBar >= 0 else i
    I[n_, I_LASTTOUCH] = i
    I[n_, I_INTOUCH] = 1 if (h >= pr - touchTol and l <= pr + touchTol) else 0
    I[n_, I_REFVER] = -1; I[n_, I_KIND] = kind; I[n_, I_PARENT] = -1; I[n_, I_KEYTYPE] = -1


@njit(cache=True)
def _add_level(F, I, n_, p, kind, dirn, pivBar, mtfW, mtfBit, vol, disp, i, day, c, h, l, mergeTol, eqTol,
               touchTol, minBars, uid, EV, ne, v2):
    """f_addLevel. returns (n_, idx, uid, ne, created)."""
    pr = np.round(p / TICK) * TICK
    idx = -1; best = mergeTol
    for j in range(n_):
        if v2 and (I[j, I_DEAD] == 1 or I[j, I_BRKDIR] != 0):
            continue
        d = abs(pr - F[j, F_PRICE])
        if d <= best:
            best = d; idx = j
    created = False
    if idx >= 0:
        j = idx
        if kind == 1 and I[j, I_SWHITS] > 0 and I[j, I_DIR] == dirn and abs(pr - F[j, F_PRICE]) <= eqTol \
                and abs(pivBar - I[j, I_LASTSW]) >= minBars:
            intact = I[j, I_SIDE] == -1 if dirn == 1 else I[j, I_SIDE] == 1
            if intact:
                I[j, I_EQHITS] += 1
        F[j, F_TOP] = max(F[j, F_TOP], pr); F[j, F_BOT] = min(F[j, F_BOT], pr)
        if I[j, I_DIR] != dirn:
            I[j, I_DIR] = 0
    else:
        j = n_
        _new_slot(F, I, n_, pr, i, day, dirn, c, h, l, touchTol, uid, 0, pivBar)
        uid += 1; n_ += 1; created = True
    if kind == 1:
        I[j, I_SWHITS] += 1; I[j, I_LASTSW] = pivBar; I[j, I_KIND] |= 1
    elif kind == 2:
        I[j, I_MAJOR] = 1; I[j, I_LASTSW] = pivBar; I[j, I_KIND] |= 2
    elif kind == 3:
        I[j, I_RANGEHITS] += 1; I[j, I_KIND] |= 4
    elif kind == 4:
        F[j, F_MTF] += mtfW; I[j, I_MTFMASK] |= mtfBit; I[j, I_KIND] |= 8
    if vol: I[j, I_VOLHIT] = 1
    if disp: I[j, I_DISPHIT] = 1
    I[j, I_LASTREACT] = day; I[j, I_REFVER] = -1
    # log create / merge
    if ne < EV.shape[0]:
        r = EV[ne]
        r[:] = np.nan
        r[0] = i; r[1] = I[j, I_UID]; r[2] = 0; r[3] = EV_CREATE if created else EV_MERGE; r[4] = kind
        r[5] = F[j, F_PRICE]; r[6] = F[j, F_TOP]; r[7] = F[j, F_BOT]; r[44] = pr; r[45] = mtfBit
        r[32] = I[j, I_KIND]; r[30] = day
        ne += 1
    return n_, j, uid, ne, created


@njit(cache=True)
def _remove(F, I, n_, j):
    for k in range(j, n_ - 1):
        F[k, :] = F[k + 1, :]; I[k, :] = I[k + 1, :]
    return n_ - 1


@njit(cache=True)
def run(o, h, l, c, A, mergeTol, eqTol, touchTol, breakBuf, dayIndex, vwap, volSw, volMaj, keys, refVersion,
        ph, pl, mph, mpl, winLo, winHi, aftLo, aftHi, mWinLo, mWinHi, mAftLo, mAftHi, rwHi, rwLo,
        htf_nb, htf_h, htf_l, htf_w, htf_bit, htf_on, mod,
        swLen, majLen, minProm, minLeg, majProm, minBars, dispATR, rangeLen, rangeMin, rangeATR, rangeTests,
        rejATR, touchCool, fakeBars, retestMove, retestMax, histDays, maxLevels, decay,
        shadow_atr, with_keys, with_shadows, max_events, v2, cap):
    n = len(c)
    EV = np.full((max_events, NE), np.nan)
    ne = 0
    # pools
    SF = np.zeros((cap, NF)); SI = np.zeros((cap, NI), np.int64); sn = 0
    KF = np.zeros((40, NF)); KI = np.zeros((40, NI), np.int64); kn = 0
    HF = np.zeros((2 * cap, NF)); HI = np.zeros((2 * cap, NI), np.int64); hn = 0
    overflow = 0
    uid = 0
    lastSHp = np.nan; lastSHb = -100000; lastSLp = np.nan; lastSLb = -100000
    rActive = False; rHi = np.nan; rLo = np.nan; rStart = 0; rHiTests = 0; rLoTests = 0
    rHiIn = False; rLoIn = False; rEndBar = -100000
    nkeys = keys.shape[1]
    # per-bar summary of the structural pool (for features / charts)
    n_levels = np.zeros(n, np.int64)
    for i in range(n):
        a = A[i]
        if np.isnan(a):
            continue
        day = dayIndex[i]
        mt = mergeTol[i]; tt = touchTol[i]; bb = breakBuf[i]
        # ---------------- 1) interactions
        ne = _interact(i, 0, SF, SI, sn, h[i], l[i], c[i], a, tt, bb, day, rejATR, touchCool, fakeBars,
                       retestMove, retestMax, EV, ne, SF, SI, sn, KF, kn, v2)
        if with_keys:
            ne = _interact(i, 1, KF, KI, kn, h[i], l[i], c[i], a, tt, bb, day, rejATR, touchCool, fakeBars,
                           retestMove, retestMax, EV, ne, SF, SI, sn, KF, kn, v2)
        if with_shadows:
            ne = _interact(i, 2, HF, HI, hn, h[i], l[i], c[i], a, tt, bb, day, rejATR, touchCool, fakeBars,
                           retestMove, retestMax, EV, ne, SF, SI, sn, KF, kn, v2)
        # ---------------- 2) new levels
        created_prices = np.empty(32); created_uids = np.empty(32, np.int64); ncr = 0
        if not np.isnan(ph[i]):
            pb = i - swLen
            promOK = ph[i] - winLo[i] >= minProm * a
            legOK = np.isnan(lastSLp) or ph[i] - lastSLp >= minLeg * a
            gapOK = pb - lastSHb >= minBars
            if promOK and legOK and gapOK:
                sn, j, uid, ne, cr = _add_level(SF, SI, sn, ph[i], 1, 1, pb, 0.0, 0, volSw[i],
                                                ph[i] - aftLo[i] >= dispATR * a, i, day, c[i], h[i], l[i], mt,
                                                eqTol[i], tt, minBars, uid, EV, ne, v2)
                if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
                lastSHp = ph[i]; lastSHb = pb
        if not np.isnan(pl[i]):
            pb = i - swLen
            promOK = winHi[i] - pl[i] >= minProm * a
            legOK = np.isnan(lastSHp) or lastSHp - pl[i] >= minLeg * a
            gapOK = pb - lastSLb >= minBars
            if promOK and legOK and gapOK:
                sn, j, uid, ne, cr = _add_level(SF, SI, sn, pl[i], 1, -1, pb, 0.0, 0, volSw[i],
                                                aftHi[i] - pl[i] >= dispATR * a, i, day, c[i], h[i], l[i], mt,
                                                eqTol[i], tt, minBars, uid, EV, ne, v2)
                if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
                lastSLp = pl[i]; lastSLb = pb
        if (not np.isnan(mph[i])) and mph[i] - mWinLo[i] >= majProm * a:
            sn, j, uid, ne, cr = _add_level(SF, SI, sn, mph[i], 2, 1, i - majLen, 0.0, 0, volMaj[i],
                                            mph[i] - mAftLo[i] >= dispATR * a, i, day, c[i], h[i], l[i], mt,
                                            eqTol[i], tt, minBars, uid, EV, ne, v2)
            if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
        if (not np.isnan(mpl[i])) and mWinHi[i] - mpl[i] >= majProm * a:
            sn, j, uid, ne, cr = _add_level(SF, SI, sn, mpl[i], 2, -1, i - majLen, 0.0, 0, volMaj[i],
                                            mAftHi[i] - mpl[i] >= dispATR * a, i, day, c[i], h[i], l[i], mt,
                                            eqTol[i], tt, minBars, uid, EV, ne, v2)
            if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
        for t_ in range(htf_nb.shape[1]):
            if htf_on[t_] and htf_nb[i, t_]:
                if not np.isnan(htf_h[i, t_]):
                    sn, j, uid, ne, cr = _add_level(SF, SI, sn, htf_h[i, t_], 4, 1, -1, htf_w[t_], htf_bit[t_],
                                                    False, False, i, day, c[i], h[i], l[i], mt, eqTol[i], tt,
                                                    minBars, uid, EV, ne, v2)
                    if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
                if not np.isnan(htf_l[i, t_]):
                    sn, j, uid, ne, cr = _add_level(SF, SI, sn, htf_l[i, t_], 4, -1, -1, htf_w[t_], htf_bit[t_],
                                                    False, False, i, day, c[i], h[i], l[i], mt, eqTol[i], tt,
                                                    minBars, uid, EV, ne, v2)
                    if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
        # range detection
        if not rActive:
            if i >= rangeLen and rwHi[i] - rwLo[i] <= rangeATR * a and i - rangeLen + 1 >= rEndBar:
                rActive = True; rHi = rwHi[i]; rLo = rwLo[i]; rStart = i - rangeLen + 1
                rHiTests = 0; rLoTests = 0
                pH = False; pL = False
                for k in range(rangeLen - 1, -1, -1):
                    tH = h[i - k] >= rHi - tt
                    tL = l[i - k] <= rLo + tt
                    if tH and not pH: rHiTests += 1
                    if tL and not pL: rLoTests += 1
                    pH = tH; pL = tL
                rHiIn = pH; rLoIn = pL
        else:
            brkUpR = c[i] > rHi + bb
            brkDnR = c[i] < rLo - bb
            tooWide = max(rHi, h[i]) - min(rLo, l[i]) > rangeATR * 1.5 * a
            if brkUpR or brkDnR or tooWide:
                if i - rStart >= rangeMin:
                    if rHiTests >= rangeTests:
                        sn, j, uid, ne, cr = _add_level(SF, SI, sn, rHi, 3, 1, rStart, 0.0, 0, False, False, i, day,
                                                        c[i], h[i], l[i], mt, eqTol[i], tt, minBars, uid, EV, ne, v2)
                        if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
                        if brkUpR and SI[j, I_CREATED] == i:
                            SI[j, I_BRK] += 1; SI[j, I_BRKDIR] = 1; SI[j, I_BRKBAR] = i; SI[j, I_BRKMOVED] = 0
                    if rLoTests >= rangeTests:
                        sn, j, uid, ne, cr = _add_level(SF, SI, sn, rLo, 3, -1, rStart, 0.0, 0, False, False, i, day,
                                                        c[i], h[i], l[i], mt, eqTol[i], tt, minBars, uid, EV, ne, v2)
                        if cr and ncr < 32: created_prices[ncr] = SF[j, F_PRICE]; created_uids[ncr] = SI[j, I_UID]; ncr += 1
                        if brkDnR and SI[j, I_CREATED] == i:
                            SI[j, I_BRK] += 1; SI[j, I_BRKDIR] = -1; SI[j, I_BRKBAR] = i; SI[j, I_BRKMOVED] = 0
                rActive = False; rEndBar = i
            else:
                tH = h[i] >= rHi - tt
                tL = l[i] <= rLo + tt
                if tH and not rHiIn: rHiTests += 1
                if tL and not rLoIn: rLoTests += 1
                rHiIn = tH; rLoIn = tL
                rHi = max(rHi, h[i]); rLo = min(rLo, l[i])
        # research: key-level pool (a new instance whenever a reference value changes)
        if with_keys:
            for kt in range(nkeys):
                v = keys[i, kt]
                pv = keys[i - 1, kt] if i > 0 else np.nan
                changed = (np.isnan(v) != np.isnan(pv)) or ((not np.isnan(v)) and v != pv)
                if changed:
                    for j in range(kn):
                        if KI[j, I_KEYTYPE] == kt:
                            kn = _remove(KF, KI, kn, j)
                            break
                    if not np.isnan(v):
                        _new_slot(KF, KI, kn, v, i, day, 0, c[i], h[i], l[i], tt, uid, 16, -1)
                        KI[kn, I_KEYTYPE] = kt
                        uid += 1; kn += 1
        # research: shadow (placebo) levels for each newly created structural level
        if with_shadows:
            for q in range(ncr):
                for sgn in (-1.0, 1.0):
                    if hn < HF.shape[0]:
                        pr = np.round((created_prices[q] + sgn * shadow_atr * a) / TICK) * TICK
                        _new_slot(HF, HI, hn, pr, i, day, 0, c[i], h[i], l[i], tt, uid, 32, -1)
                        HI[hn, I_PARENT] = created_uids[q]
                        uid += 1; hn += 1
        # ---------------- 3) scoring + pruning
        for j in range(sn):
            SI[j, I_NEARVWAP] = 1 if (not np.isnan(vwap[i])) and abs(vwap[i] - SF[j, F_PRICE]) <= mt else 0
            if SI[j, I_REFVER] != refVersion[i]:
                cnt = 0
                for kt in range(nkeys):
                    if kt >= 11 and np.isnan(keys[i, kt]):
                        continue
                    pk = keys[i, kt]
                    if (not np.isnan(pk)) and pk >= SF[j, F_BOT] - mt and pk <= SF[j, F_TOP] + mt:
                        cnt += 1
                SI[j, I_REFCOUNT] = cnt; SI[j, I_REFVER] = refVersion[i]
            cc = 1.0 * min(SI[j, I_SWHITS], 2) + (1.5 if SI[j, I_MAJOR] else 0.0) + 1.5 * min(SI[j, I_RANGEHITS], 2) \
                + 1.5 * min(SI[j, I_EQHITS], 2) + 1.0 * min(SF[j, F_MTF], 4.0) + 1.5 * min(SI[j, I_REFCOUNT], 3) \
                + (0.5 if SI[j, I_NEARVWAP] else 0.0) + 0.5 * min(SI[j, I_TOUCHES], 6) + 0.75 * min(SI[j, I_REJ], 4) \
                + 1.0 * min(SI[j, I_RET], 3) + 1.25 * min(SI[j, I_FAKE], 3) + (0.5 if SI[j, I_VOLHIT] else 0.0) \
                + (1.0 if SI[j, I_DISPHIT] else 0.0) \
                - 0.5 * min(max(SI[j, I_BRK] - SI[j, I_RET] - SI[j, I_FAKE] - 1, 0), 4)
            cc = max(cc, 0.0)
            s = cc * decay ** (day - SI[j, I_LASTREACT])
            SF[j, F_CONF] = cc; SF[j, F_STR] = s
            SI[j, I_RANK] = 3 if s >= 7.0 else (2 if s >= 5.0 else (1 if s >= 3.0 else 0))
            if SI[j, I_RANK] == 3: SI[j, I_EVERHC] = 1
        j = sn - 1
        while j >= 0:
            if day - SI[j, I_LASTREACT] > histDays or day - SI[j, I_BORNDAY] > histDays * 2:
                if ne < EV.shape[0]:
                    EV[ne, :] = np.nan; EV[ne, 0] = i; EV[ne, 1] = SI[j, I_UID]; EV[ne, 2] = 0; EV[ne, 3] = EV_REMOVE
                    EV[ne, 5] = SF[j, F_PRICE]; EV[ne, 32] = SI[j, I_KIND]; ne += 1
                sn = _remove(SF, SI, sn, j)
            j -= 1
        while sn > maxLevels:
            wi = 0; ws = 1e10
            for j in range(sn):
                if SF[j, F_STR] < ws:
                    ws = SF[j, F_STR]; wi = j
            if ne < EV.shape[0]:
                EV[ne, :] = np.nan; EV[ne, 0] = i; EV[ne, 1] = SI[wi, I_UID]; EV[ne, 2] = 0; EV[ne, 3] = EV_REMOVE
                EV[ne, 5] = SF[wi, F_PRICE]; EV[ne, 32] = SI[wi, I_KIND]; ne += 1
            sn = _remove(SF, SI, sn, wi)
        if v2:
            j = sn - 1
            while j >= 0:
                if SI[j, I_DEAD] == 1:
                    if ne < EV.shape[0]:
                        EV[ne, :] = np.nan; EV[ne, 0] = i; EV[ne, 1] = SI[j, I_UID]; EV[ne, 2] = 0; EV[ne, 3] = EV_REMOVE
                        EV[ne, 5] = SF[j, F_PRICE]; EV[ne, 32] = SI[j, I_KIND]; ne += 1
                    sn = _remove(SF, SI, sn, j)
                j -= 1
            j = kn - 1
            while j >= 0:
                if KI[j, I_DEAD] == 1:
                    kn = _remove(KF, KI, kn, j)
                j -= 1
            j = hn - 1
            while j >= 0:
                if HI[j, I_DEAD] == 1 or day - HI[j, I_LASTREACT] > histDays or day - HI[j, I_BORNDAY] > histDays * 2:
                    hn = _remove(HF, HI, hn, j)
                j -= 1
            if sn > cap - 40 or hn > 2 * cap - 80:
                overflow += 1
        if with_shadows and not v2:
            j = hn - 1
            while j >= 0:
                alive = False
                for q in range(sn):
                    if SI[q, I_UID] == HI[j, I_PARENT]:
                        alive = True
                        break
                if not alive:
                    hn = _remove(HF, HI, hn, j)
                j -= 1
        n_levels[i] = sn
    if overflow > 0:
        n_levels[0] = -overflow
    return EV[:ne], n_levels


def run_engine(b, p=P, with_keys=True, with_shadows=True, max_events=6_000_000, v2=False, cap=CAP):
    x = precompute(b, p)
    EV, nlev = run(x["o"], x["h"], x["l"], x["c"], x["atr"], x["mergeTol"], x["eqTol"], x["touchTol"], x["breakBuf"],
                   x["dayIndex"], x["vwap"], x["volSw"], x["volMaj"], x["keys"], x["refVersion"],
                   x["ph"], x["pl"], x["mph"], x["mpl"], x["winLo"], x["winHi"], x["aftLo"], x["aftHi"],
                   x["mWinLo"], x["mWinHi"], x["mAftLo"], x["mAftHi"], x["rwHi"], x["rwLo"],
                   x["htf_nb"], x["htf_h"], x["htf_l"], x["htf_w"], x["htf_bit"], x["htf_on"], x["mod"],
                   p["swLen"], p["majLen"], p["minProm"], p["minLeg"], p["majProm"], p["minBars"], p["dispATR"],
                   p["rangeLen"], p["rangeMin"], p["rangeATR"], p["rangeTests"], p["rejATR"], p["touchCool"],
                   p["fakeBars"], p["retestMove"], p["retestMax"], p["histDays"], p["maxLevels"], p["decay"],
                   SHADOW_ATR, with_keys, with_shadows, max_events, v2, cap)
    ev = pd.DataFrame(EV, columns=EVCOLS)
    for col in ["bar", "uid", "pool", "etype", "edir"]:
        ev[col] = ev[col].fillna(0).astype(np.int64)
    if len(ev) >= max_events:
        raise RuntimeError("event buffer full")
    if nlev[0] < 0:
        raise RuntimeError(f"pool overflow on {-nlev[0]} bars")
    return ev, nlev, x

KEYNAMES = ["PDH", "PDL", "PDC", "PWH", "PWL", "ONH", "ONL", "LDNH", "LDNL", "pRTHH", "pRTHL", "ORH", "ORL"]
ETNAMES = {1: "TOUCH", 2: "REJECT", 3: "SWEEP", 4: "BREAK", 5: "FAKE", 6: "RETEST", 7: "CREATE", 8: "REMOVE", 9: "MERGE"}

# fixed research splits (decided BEFORE looking at any level statistic)
TRAIN = ("2023-01-01", "2024-06-30")
VAL = ("2024-07-01", "2024-12-31")
OOS = ("2025-01-01", "2025-12-31")


def split_of(tday):
    t = pd.to_datetime(tday)
    return np.where(t < pd.Timestamp(TRAIN[0]), "warmup",
                    np.where(t <= pd.Timestamp(TRAIN[1]), "train",
                             np.where(t <= pd.Timestamp(VAL[1]), "val", "oos")))
