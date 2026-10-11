import numpy as np, pandas as pd
G = pd.read_pickle('output/E_minute_sums.pkl')
G.columns = ['_'.join(c) for c in G.columns]
G = G.reset_index()
def lbl(sm): t = (18*60+sm) % 1440; return f'{t//60:02d}:{t%60:02d}'
rows = []
for s in range(0, 1380, 5):
    for L in (15, 30, 45, 60, 90, 120, 180):
        if s + L > 1380: continue
        w = G[(G.sm >= s) & (G.sm < s + L)]
        r = {'start': lbl(s), 'sm': s, 'len': L}
        for yr in (2023, 2024, 2025, 'all'):
            y = w if yr == 'all' else w[w.yr == yr]
            ev = y[(y.bin >= 1) & y.agree]; ctl = y[y.bin >= 0]
            for k in ('w0.25', 'w0.5', 'w1.0', 'fe30'):
                pe = ev[k + '_sum'].sum() / ev[k + '_count'].sum(); pc = ctl[k + '_sum'].sum() / ctl[k + '_count'].sum()
                r[f'{k}_{yr}'] = pe - pc if k != 'fe30' else pe
            r[f'n_{yr}'] = ev['w0.5_count'].sum()
        rows.append(r)
M = pd.DataFrame(rows)
for k in ('w0.25', 'w0.5', 'w1.0', 'fe30'):
    M[f'{k}_min'] = M[[f'{k}_{y}' for y in (2023, 2024, 2025)]].min(1)
M.to_pickle('output/F_map.pkl')
pd.set_option('display.width', 250, 'display.max_rows', 300)
cols = ['start', 'len', 'n_all', 'w0.25_all', 'w0.5_all', 'w0.5_2023', 'w0.5_2024', 'w0.5_2025', 'w0.5_min', 'w1.0_min', 'fe30_all', 'fe30_min']
for L in (30, 60, 90, 120):
    m = M[M.len == L]
    print(f'--- len {L}: top 15 by min-over-years edge(+0.5R) ---')
    print(m.sort_values('w0.5_min', ascending=False)[cols].head(15).round(3).to_string(index=False))
    print(f'--- len {L}: top 10 by min-over-years fe30 ---')
    print(m.sort_values('fe30_min', ascending=False)[cols].head(10).round(3).to_string(index=False))
