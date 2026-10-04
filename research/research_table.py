from wf import *
import glob
idea={'F1_vwap_reentry':'VWAP-σ-Band Re-Entry (Mean Reversion)','F2_trend_pullback':'Trend-Pullback an EMA/VWAP','F3_ORB':'Opening-Range-Breakout',
'F4_OR_fade':'Opening-Range-Fake-Out-Fade','F5_RSI_extreme':'RSI-Extrem + Trendfilter','F6_mom_burst':'Momentum-Burst-Fortsetzung','F6b_mom_refined':'Momentum-Burst + Trend/Volumen/Zeit-Filter',
'F7_consec_dip':'N Gegenbars im Trend (Dip-Buy)','F8_quiet_fade':'Fade neuer Extreme an ruhigen Tagen','F9_gap_fill':'Gap-Fill zum Vortagesschluss','F11_z_lowvol':'Z-Score-Reversion bei niedriger Vola',
'F12_time_drift':'Tageszeit-Drift (feste Minute)','F13_limit_levels':'Limit an PDH/PDL/OR/VWAP-Bändern','F14_impulse_retrace_limit':'Impuls → Retracement-Limit','F14b_retrace_filtered':'Impuls-Retracement + Regimefilter',
'F15_break_retest':'Break & Retest (Limit am Level)','F16_regime_vwap_dip':'Daily-Regime + VWAP-Dip','F17_capitulation':'Kapitulations-Kerze Fade','F18_vwap_band_limit':'VWAP-Band-Limit-Reversion',
'F19_trendday_pullback':'Trend-Tag (IB-Extension) Pullback','F20_inside5m_breakout':'5-min Inside-Bar-Breakout','F21_premarket_breakout':'Pre-Market-Range-Breakout'}
nd=df[df.sd>='2024-01-01'].sd.nunique(); rows=[]
for f in sorted(glob.glob('tr_F*.pkl'),key=lambda x:int(''.join(ch for ch in x.split('_')[1][1:] if ch.isdigit()))):
    fam=f[3:-4]; tr=pd.read_pickle(f)
    for fmin in (0.5,2):
        O,sel=wf_select(tr,fmin)
        if len(O)==0: rows.append(dict(Version=fam,Idee=idea.get(fam,''),Kombis=len(tr),fmin=fmin,N_OOS=0)); continue
        st=stats(O,nd); act=stats(O)
        isw=np.mean([s[2] for s in sel if s])
        rows.append(dict(Version=fam,Idee=idea.get(fam,''),Kombis=len(tr),fmin=fmin,WR_IS=round(isw,1),WR_WF_OOS=st['WR'],N_OOS=st['N'],PF=st['PF'],ExpR=st['ExpR'],AvgWinR=st['AvgWinR'],AvgLossR=st['AvgLossR'],MaxDD_R=st['MaxDD_R'],MaxLS=st['MaxLS'],MaxWS=st['MaxWS'],TPD_alle=st['TPD'],TPD_aktiv=act['TPD']))
R=pd.DataFrame(rows); R.to_csv('research_table.csv',index=False); print(R.to_string(index=False))
