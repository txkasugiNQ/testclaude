from hw_lab import *
H = HW(2); b = H.b
rng = np.random.default_rng(0)
idx = np.where((b.tod >= 720) & (b.tod < 950) & (b.split != 'OOS'))[0]
idx = np.sort(rng.choice(idx, 15000, replace=False))
side = rng.choice([-1, 1], len(idx))
ev = H.market(idx, side)
rr = [0.25, 0.33, 0.5, 0.67, 0.75, 1.0]; ss = [0.5, 1.0, 2.0]; holds = [10, 30, 10000]
ev, R = H.run(ev, b.atr[ev.sig.values], rr, ss, holds)
D = summarize(ev, R, rr, ss, holds)
D['wr_baseline'] = 1/(1+D.tgt)
pd.set_option('display.width', 200)
print(D[D.hold==10000][['stop','tgt','n_IS','wr_IS','wr_VAL','wr_baseline','exp_IS','exp_VAL']].round(3).to_string())
print(D[(D.hold==30)&(D.stop==1.0)][['stop','tgt','hold','wr_IS','exp_IS','al_IS','aw_IS']].round(3).to_string())
