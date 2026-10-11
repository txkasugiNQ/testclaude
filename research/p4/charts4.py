import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
S = ['#2a78d6', '#eb6834', '#1baf7a', '#e34948']; INK2, GRID, SURF = '#52514e', '#e4e3df', '#fcfcfb'
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2,
                     'ytick.color': INK2, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.spines.top': False,
                     'axes.spines.right': False, 'font.size': 9, 'lines.linewidth': 2})
O = '../output/'
fig, ax = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={'width_ratios': [1.5, 1]})
for i, (k, lab) in enumerate((('V2', 'V2: Range ≥ 0.20·DR (5 Trades/Monat)'), ('V1', 'V1: ohne Größenfilter (10 Trades/Monat)'))):
    T = pd.read_pickle(O + f'p4_final_{k}.pkl').sort_values('e')
    ax[0].plot(pd.DatetimeIndex(T.sess), T.pnl.cumsum(), color=S[i], label=lab)
ax[0].axvspan(pd.Timestamp('2025-01-01'), pd.Timestamp('2025-12-12'), color=S[2], alpha=0.07, lw=0)
ax[0].text(pd.Timestamp('2025-01-15'), 3, 'Out-of-Sample 2025', color=INK2)
ax[0].set_ylabel('kumuliert (R)'); ax[0].legend(frameon=False, loc='upper left')
ax[0].set_title('Sweep & Reclaim der 08:12–09:12-Range (09:12–09:30), fester TP 2R / SL 1R', loc='left')
G = pd.read_pickle(O + 'p4_sizefilter.pkl'); g = G[(G.range == '08:12-09:12') & (G.we == 570)]
pv = g.pivot_table(index='min_rng', columns=['buf', 'tp'], values='min_y')
DIV = LinearSegmentedColormap.from_list('div', ['#c0392b', '#e34948', '#f0efec', '#3987e5', '#1c5cab'])
im = ax[1].imshow(pv.values, cmap=DIV, norm=TwoSlopeNorm(0, -0.4, 0.4), aspect='auto', origin='lower'); ax[1].grid(False)
ax[1].set_xticks(range(pv.shape[1]), [f'{b}/{t}R' for b, t in pv.columns], rotation=60, fontsize=7)
ax[1].set_yticks(range(pv.shape[0]), [f'≥{v}' for v in pv.index]); ax[1].set_ylabel('Mindest-Range (× DR)'); ax[1].set_xlabel('SL-Puffer (× Range) / TP')
for i in range(pv.shape[0]):
    for j in range(pv.shape[1]):
        ax[1].text(j, i, f'{pv.values[i, j]:.2f}', ha='center', va='center', fontsize=6.5)
ax[1].set_title('Plateau: schlechtestes Jahr (R/Trade)', loc='left')
fig.tight_layout(); fig.savefig(O + 'p4_fig1.png', dpi=130); print('ok')
