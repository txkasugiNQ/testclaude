from lab import *
import sys
tf = int(sys.argv[1]) if len(sys.argv)>1 else 2
b = B(tf); L = daylevels(b)
pm = (b.tod >= 720) & (b.tod < 960)
c, h, l, vw, atr = b.c, b.h, b.l, b.vw, b.atr
day = b.day
# bars since last VWAP touch (touch = low<=vw<=high)
touch = (l <= vw) & (h >= vw)
above = l > vw; below = h < vw
def run_len(mask):
    out = np.zeros(len(mask), int); cnt = 0
    for i in range(len(mask)):
        if i>0 and day[i]!=day[i-1]: cnt = 0
        cnt = cnt+1 if mask[i] else 0
        out[i] = cnt
    return out
ra = run_len(above); rb = run_len(below)
# max excursion away from vwap during the current run, in ATR
dist_up = (h - vw)/atr; dist_dn = (vw - l)/atr
def run_max(x, runlen):
    out = np.zeros(len(x)); cur = 0
    for i in range(len(x)):
        cur = max(cur, x[i]) if runlen[i] > 1 else (x[i] if runlen[i]==1 else 0)
        out[i] = cur
    return out
mu = run_max(dist_up, ra); md = run_max(dist_dn, rb)
for N in [10, 20, 40]:
  for K in [2, 4]:
    for stop_atr in [0.75, 1.5]:
        rows=[]
        # setup known at close of bar i: was above vwap for >=N bars with max dist >=K ATR. Place buy limit at vwap for next bar
        for side, rl_, mx in [(1, ra, mu), (-1, rb, md)]:
            cond = pm & (rl_ >= N) & (mx >= K)
            idx = np.where(cond)[0]
            e = vw[idx] + side*0.25*0   # limit exactly at current vwap
            rows.append(pd.DataFrame(dict(sb=idx, side=side, etype=2, eprice=e, sl=e - side*stop_atr*atr[idx], expiry=1)))
        sig = pd.concat(rows)
        sig = sig[sig.split if False else slice(None)] if False else sig
        ladder(b, sig, ks=(1,1.5,2,3), label=f'H2 first VWAP touch tf={tf} N={N} K={K} stopATR={stop_atr}', max_per_day=2)
