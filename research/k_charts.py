"""Charts for the time-window research report (static PNG, light theme, reference palette)."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'text.color': INK, 'axes.grid': True, 'grid.color': GRID,
                     'grid.linewidth': 0.6, 'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 9,
                     'lines.linewidth': 2})
DIV = LinearSegmentedColormap.from_list('div', ['#c0392b', '#e34948', '#f0efec', '#3987e5', '#1c5cab'])
YC = {2023: S1, 2024: S2, 2025: S3}
def hm(h):  # 'HH:MM' -> plotting x in hours since 18:00
    a, b = map(int, h.split(':')); return ((a*60+b-18*60) % 1440) / 60
ticks = [hm(t) for t in ('18:00', '21:00', '00:00', '03:00', '06:00', '09:30', '12:00', '15:00', '17:00')]
tlbl = ['18:00', '21:00', '00:00', '03:00', '06:00', '09:30', '12:00', '15:00', '17:00']

# ---------- Fig 1: 24h profile ----------
P = pd.read_csv('output/A_profile_IS.csv', index_col=0); P2 = pd.read_csv('output/A_profile_OOS.csv', index_col=0)
V = pd.read_csv('output/D_vr.csv', header=[0, 1], index_col=0)
I = pd.read_pickle('output/I_grid_ev.pkl')
fig, ax = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
x = [((i - 18*60) % 1440)/60 for i in P.index]
o = np.argsort(x)
ax[0].plot(np.array(x)[o], P.tr_pts.values[o], color=S1, label='2023–2024'); ax[0].plot(np.array(x)[o], P2.tr_pts.values[o], color=S2, label='2025')
ax[0].set_ylabel('Ø 1-min True Range (Pkt)'); ax[0].legend(frameon=False); ax[0].set_title('A  Volatilität nach Tageszeit (5-min Buckets, ET)', loc='left')
for yr in (2023, 2024, 2025):
    xs = [hm(s)+0.5 for s in V.index]
    ax[1].plot(xs, V[('VR15', str(yr))], color=YC[yr], label=str(yr), marker='o', ms=3, lw=1.5)
ax[1].axhline(1, color=INK2, lw=1, ls='--'); ax[1].set_ylabel('Varianz-Ratio VR(15)\n>1 = Trend, <1 = Mean-Rev.')
ax[1].set_title('B  Persistenz: Varianz-Ratio der 60-min-Fenster je Jahr', loc='left'); ax[1].legend(frameon=False, ncol=3)
g = I[(I.tf == 1) & (I.trig == 'IMP') & (I.len == 30)]
for yr in (2023, 2024, 2025):
    ax[2].plot([hm(s)+0.25 for s in g.start], g[f'w1_{yr}'], color=YC[yr], label=str(yr), lw=1.5, marker='o', ms=3)
g15 = I[(I.tf == 15) & (I.trig == 'IMP') & (I.len == 90)]
ax[2].axhline(0, color=INK2, lw=1, ls='--')
ax[2].set_ylabel('EV-Edge vs. Zufall (R)\nBracket +1R/−1R'); ax[2].set_title('C  Continuation-Edge 1-min-Impuls, 30-min-Fenster, je Jahr', loc='left')
ax[2].legend(frameon=False, ncol=3); ax[2].set_xticks(ticks, tlbl); ax[2].set_xlabel('Uhrzeit ET (Session 18:00 → 17:00)')
for a in ax:
    for (s, e) in (('09:30', '12:00'), ('12:00', '14:30')):
        a.axvspan(hm(s), hm(e), color=S1, alpha=0.06, lw=0)
fig.tight_layout(); fig.savefig('output/fig1_profile_24h.png', dpi=130); plt.close()

# ---------- Fig 2: heatmaps start x len, min-over-years edge ----------
fig, axs = plt.subplots(2, 4, figsize=(16, 8))
for col, tf in enumerate((1, 3, 5, 15)):
    for row, trig in enumerate(('IMP', 'PB')):
        g = I[(I.tf == tf) & (I.trig == trig)]
        piv = g.pivot(index='len', columns='sm', values='w1_min')
        piv = piv.where(g.pivot(index='len', columns='sm', values='n_all') >= 150)
        a = axs[row, col]
        im = a.imshow(piv.values, aspect='auto', cmap=DIV, norm=TwoSlopeNorm(0, -0.1, 0.1), origin='lower')
        xs = piv.columns.values; xt = [i for i, s in enumerate(xs) if (s % 180 == 0 and s != 900) or s == 930]
        a.set_xticks(xt, [f'{(18*60+xs[i])//60%24:02d}:{(18*60+xs[i])%60:02d}' for i in xt], rotation=45)
        a.set_yticks(range(len(piv.index)), piv.index); a.grid(False)
        a.set_title(f'{trig}  tf={tf}m  (schlechtestes Jahr)', loc='left')
        if col == 0: a.set_ylabel('Fensterlänge (min)')
fig.colorbar(im, ax=axs, shrink=0.6, label='EV-Edge vs. Kontrolle, min über 2023/24/25 (R)')
fig.suptitle('Plateau-Karte: Startzeit × Länge, blau = Continuation-Vorteil in ALLEN drei Jahren', x=0.01, ha='left')
fig.savefig('output/fig2_plateau_heatmaps.png', dpi=120, bbox_inches='tight'); plt.close()

# ---------- Fig 3: BE question + MAE ----------
J = pd.read_csv('output/J_behavior.csv')
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
xs = np.array([0.15, 0.2, 0.3, 0.5])
ax[0].plot(xs, 1 - xs, color=INK2, ls='--', lw=1.5, label='Random Walk: 1 − x')
for (w, trig, c, lab) in (('NY-AM 09:45-11:45', 'IMP', S1, 'NY-AM Impuls (1m)'), ('NY-MID 12:15-14:15', 'IMP', S2, 'NY-MID Impuls (1m)'),
                          ('NY-MID 12:15-14:15', 'CTRL', S3, 'Zufalls-Entry (1m)')):
    r = J[(J.tf == 1) & (J.window == w) & (J.trig == trig)].iloc[0]
    ax[0].plot(xs, [r[f'P(BE before +1R | +{x})'] for x in xs], color=c, marker='o', ms=6, label=lab)
ax[0].set_xlabel('Trade hat +x R erreicht'); ax[0].set_ylabel('P(zurück auf Entry vor +1R)')
ax[0].set_title('A  Früher BE: wie oft wird ein späterer +1R-Trade abgewürgt?', loc='left'); ax[0].legend(frameon=False)
for tf, c in ((1, S1), (3, S2), (5, S3)):
    sub = J[(J.trig == 'IMP') & (J.tf == tf) & J.window.isin(['NY-AM 09:45-11:45', 'NY-MID 12:15-14:15'])]
    for _, r in sub.iterrows():
        ax[1].plot([50, 75, 90], [r['MAEpre+1R_p50'], r['MAEpre+1R_p75'], r['MAEpre+1R_p90']], color=c, marker='o', ms=6,
                   ls='-' if 'AM' in r.window else ':', label=f'tf={tf}m {r.window[:6]}')
ax[1].set_xlabel('Perzentil'); ax[1].set_ylabel('MAE vor +1R (in ATR des Timeframes)')
ax[1].set_title('B  Platzbedarf von Trades, die +1 ATR erreichen', loc='left'); ax[1].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig('output/fig3_be_mae.png', dpi=130); plt.close()
print('ok')
