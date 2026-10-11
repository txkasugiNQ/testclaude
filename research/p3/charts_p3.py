import numpy as np, pandas as pd, matplotlib, sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, '.')
from fragility import frag
S = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']; INK2, GRID, SURF = '#52514e', '#e4e3df', '#fcfcfb'
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2,
                     'ytick.color': INK2, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.spines.top': False,
                     'axes.spines.right': False, 'font.size': 9, 'lines.linewidth': 2})
O = '../output/'
names = {'A': 'A: Chandelier 20×ATR (k0.12)', 'B': 'B: TP 5R (k0.15)', 'C': 'C: 50% @+1R, Rest Trail (k0.15)'}
fig, ax = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={'width_ratios': [1.6, 1]})
for i, (k, lab) in enumerate(names.items()):
    T = pd.read_pickle(O + f'p3_cand_{k}.pkl').sort_values('e')
    ax[0].plot(pd.DatetimeIndex(T.sess), T.pnl.cumsum(), color=S[i], label=lab)
ax[0].axvspan(pd.Timestamp('2025-01-01'), pd.Timestamp('2025-12-12'), color=S[2], alpha=0.07, lw=0)
ax[0].set_ylabel('kumuliert (R)'); ax[0].legend(frameon=False, loc='upper left')
ax[0].set_title('London-Range intakt bis 09:30 → RTH-Ausbruch (09:30–11:00), ~6 Trades/Monat', loc='left')
P2 = pd.read_pickle(O + 'p2_final_trades.pkl')
items = [('Phase 2 System', P2.pnl.values)] + [(names[k][:1] + ' (London-Range)', pd.read_pickle(O + f'p3_cand_{k}.pkl').pnl.values) for k in names]
y = np.arange(len(items))
ax[1].barh(y + 0.2, [x.mean() for _, x in items], height=0.36, color=S[0], label='Expectancy alle Trades')
ax[1].barh(y - 0.2, [frag(x)['exp_wo_top5pct'] for _, x in items], height=0.36, color=S[1], label='ohne beste 5 % der Trades')
ax[1].set_yticks(y, [n for n, _ in items]); ax[1].axvline(0, color=INK2, lw=0.8); ax[1].set_xlabel('R pro Trade')
ax[1].legend(frameon=False, fontsize=8, loc='lower right'); ax[1].set_title('Ausreißer-Abhängigkeit (deine harte Regel)', loc='left')
fig.tight_layout(); fig.savefig(O + 'p3_fig1_candidates.png', dpi=130); print('ok')
