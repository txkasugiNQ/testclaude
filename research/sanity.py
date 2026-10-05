from lab import *
b = B(2)
rng = np.random.default_rng(0)
idx = np.where((b.tod>=720)&(b.tod<960)&(b.tod%10==0))[0]
idx = np.sort(idx)
side = rng.choice([-1,1], len(idx))
c = b.c[idx]
sig = pd.DataFrame(dict(sb=idx, side=side, etype=0, sl=c - side*15, tp=c + side*15))
t = b.run(sig)
report(t, b, 'random 15/15 market')
t = b.run(sig.drop(columns='tp'), be_R=0, trail_mode=1, trail_start_R=1, trail_param=1)
report(t, b, 'random trail')
