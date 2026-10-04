from wf2 import *
import glob
idea={'G1_box_oco':('Kompressions-Box, OCO-Stop-Entries an den Kanten','Range N Bars < q·ATR','Buy/Sell-Stop an Box-Kante','Box-Gegenseite / RR / EOD'),
'G2_box_close':('Kompressions-Box, Close-Bestätigung','Range N Bars < q·ATR','Close außerhalb → Market','Box/Swing-Stop, RR/EOD'),
'G3_burst_free':('Momentum-Burst, freies RR','Impuls 5 Bars > th·ATR','Market nächste Open','Swing/ATR-Stop, RR 1–3/EOD/120min'),
'G4_level_break':('Level-Breakout (PDH/PDL, ON, IB, OR30, PW, London)','1. Close jenseits Level','Market nächste Open','Level/Swing-Stop, RR/EOD/Zeit'),
'G5_trend_day':('Trend-Tag-Regel (Bewegung ab RTH-Open + Position in Range)','Zeit T, |Move|>x·ATR, äußere 25 %','Market','k·ATR-Stop, RR/EOD'),
'G6_equal_hl_break':('Equal Highs/Lows Break','≥n Tests des 60-Bar-Extrems','1. Close darüber','Swing/ATR-Stop, RR/EOD'),
'G7_opening_bar':('Opening Bar Range (09:30-Kerze)','Körper > k·ATR','Market 09:31 oder OCO-Stop an Kerzen-H/L','Kerzen-Extrem/ATR-Stop, RR/EOD/Zeit'),
'G8_burst_overnight':('Momentum-Burst Asia/London','Impuls > th·ATR (ETH)','Market','Swing-Stop, RR, Zeit'),
'G9_early_ignition':('Burst + Trend-/Zeit-/Range-Kontext','Burst + VWAP/Tagesrichtung + Range-Platz','Market / Stop-Level','Swing-Stop, RR/EOD'),
'G10_burst_level':('Momentum Burst Level (Stop-Entry)','Impuls 5 Bars > th·ATR','Buy/Sell-Stop am 5-Bar-Extrem','Gegenseite 5-Bar-Range, RR/EOD/120min')}
nd=df[df.sd>='2024-01-01'].sd.nunique(); rows=[]
for name in idea:
    tr=pd.read_pickle(f'tr2_{name}.pkl')
    if name=='G10_burst_level': variants=[('stop-only',{k:v for k,v in tr.items() if json.loads(k)['entry']=='stop'})]
    else: variants=[('',tr)]
    for vlab,trd in variants:
        for fmin in (0.25,1.0):
            O,sel=wf(trd,fmin)
            if len(O)==0: continue
            s=stats2(O,nd); a=stats2(O); isx=np.mean([x[2] for x in sel])
            py=lambda y: (lambda x: round(x.pnlR[x.pnlR>0].sum()/-x.pnlR[x.pnlR<0].sum(),2) if (x.pnlR<0).any() else np.nan)(O[O.ts.dt.year==y])
            rows.append(dict(Version=name+(' '+vlab if vlab else ''),Idee=idea[name][0],Faktoren=idea[name][1],Entry=idea[name][2],Exit=idea[name][3],Kombis=len(trd),fmin=fmin,
                IS_ExpR=round(isx,3),OOS_N=s['N'],OOS_WR=s['WR'],OOS_PF=s['PF'],OOS_ExpR=s['ExpR'],AvgWinR=s['AvgWinR'],AvgLossR=s['AvgLossR'],MaxDD_R=s['MaxDD_R'],MaxLS=s['MaxLS'],MaxWS=s['MaxWS'],
                SharpeD=s['SharpeD'],TPD_aktiv=a['TPD'],PF_2024=py(2024),PF_2025=py(2025)))
R=pd.DataFrame(rows); R.to_csv('research_table2.csv',index=False); pd.set_option('display.width',300); print(R.drop(columns=['Idee','Faktoren','Entry','Exit']).to_string(index=False))
