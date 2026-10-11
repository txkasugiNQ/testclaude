import numpy as np, pandas as pd, matplotlib, sys, os
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
S = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
INK2, GRID, SURF = '#52514e', '#e4e3df', '#fcfcfb'
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
                     'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 9, 'lines.linewidth': 2})
O = '../output/'
T = pd.read_pickle(O + 'p2_final_trades.pkl').sort_values('e')
fig, ax = plt.subplots(2, 1, figsize=(12, 7.5), gridspec_kw={'height_ratios': [3, 1.4]})
eq = T.pnl.cumsum().values; eqn = T.pnl_net.cumsum().values; dates = pd.DatetimeIndex(T.sess)
ax[0].plot(dates, eq, color=S[0], label='brutto (vor Kosten)'); ax[0].plot(dates, eqn, color=S[1], label='netto (0.6 Pkt Roundtrip)')
ax[0].axvspan(pd.Timestamp('2025-01-01'), dates.max(), color=S[2], alpha=0.08, lw=0); ax[0].text(pd.Timestamp('2025-01-10'), eq.max() * 0.95, 'Out-of-Sample 2025', color=INK2)
ax[0].set_ylabel('kumuliert (R)'); ax[0].legend(frameon=False, loc='upper left')
ax[0].set_title('Equity-Kurve: Day-Trend-Pullback-Continuation, 1 Kontrakt-Risiko = 1R, Tageslimit ±1R', loc='left')
m = T.groupby(pd.PeriodIndex(T.sess, freq='M')).pnl.sum()
ax[1].bar(m.index.to_timestamp(), m.values, width=20, color=[S[2] if v > 0 else S[7] for v in m.values])
ax[1].set_ylabel('R pro Monat'); ax[1].axhline(0, color=INK2, lw=0.8)
fig.tight_layout(); fig.savefig(O + 'p2_fig1_equity.png', dpi=130); plt.close()

F = pd.read_csv(O + 'p2_mgmt_families_final.csv')
fig, ax = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
fams = list(dict.fromkeys(F.fam))
for i, fam in enumerate(fams):
    g = F[F.fam == fam]
    for a, col, tt in ((ax[0], 'exp_IS', 'In-Sample 2023–24'), (ax[1], 'exp_OOS', 'Out-of-Sample 2025')):
        a.scatter(g.WR, g[col], s=28, color=S[i % 8], label=fam, alpha=0.85, edgecolor=SURF, lw=0.5); a.set_title(tt, loc='left')
for a in ax:
    a.axhline(0, color=INK2, lw=0.8); a.axhline(0.35, color=S[7], lw=1, ls='--'); a.text(0.3, 0.36, 'Ziel +0.35R', color=S[7], fontsize=8)
    a.set_xlabel('Winrate')
ax[0].set_ylabel('Expectancy pro Trade (R, brutto)'); ax[1].legend(frameon=False, fontsize=8, loc='upper right')
fig.suptitle('Winrate vs. Expectancy – jede Management-Variante auf denselben Entries (Punkt = eine Variante)', x=0.01, ha='left')
fig.tight_layout(); fig.savefig(O + 'p2_fig2_wr_vs_exp.png', dpi=130); plt.close()

P = pd.read_csv(O + 'p2_plateau_floor_time.csv')
DIV = LinearSegmentedColormap.from_list('div', ['#c0392b', '#e34948', '#f0efec', '#3987e5', '#1c5cab'])
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
for a, col, tt in ((ax[0], 'exp', 'Expectancy 2023–25 (R)'), (ax[1], 'min_year', 'schlechtestes Jahr (R)')):
    pv = P.pivot(index='floor', columns='maxbars', values=col)
    im = a.imshow(pv.values, cmap=DIV, norm=TwoSlopeNorm(0, -0.25, 0.25), aspect='auto', origin='lower'); a.grid(False)
    a.set_xticks(range(len(pv.columns)), pv.columns); a.set_yticks(range(len(pv.index)), pv.index)
    a.set_xlabel('Zeit-Exit (min)'); a.set_ylabel('Stop-Mindestabstand (× ATR1m)'); a.set_title(tt, loc='left')
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]):
            a.text(j, i, f'{pv.values[i, j]:.2f}', ha='center', va='center', fontsize=8, color='#0b0b0b')
fig.tight_layout(); fig.savefig(O + 'p2_fig3_plateau.png', dpi=130); plt.close()
print('ok')
