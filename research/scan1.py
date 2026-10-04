from feats import *
df=build(); L=pd.read_pickle('labels.pkl')
F=df.iloc[L.i.values].reset_index(drop=True)
c=F.c; A=F.atrD
X=pd.DataFrame({
 'vwap_dev_sig':(c-F.vrw)/F.vrs, 'vwap_dev_atr':(c-F.vrw)/A,
 'eth_vwap_dev':(c-F.vew)/F.ves,
 'z20':F.z20,'z60':F.z60,'z240':F.z240,'rsi14':F.rsi14,'rsi70':F.rsi70,
 'ret5':F.ret5/A,'ret15':F.ret15/A,'ret30':F.ret30/A,'ret60':F.ret60/A,
 'ema21_50':(F.ema21-F.ema50)/A,'ema50_200':(F.ema50-F.ema200)/A,'c_ema200':(c-F.ema200)/A,'c_ema500':(c-F.ema500)/A,
 'pos_in_range':(c-F.sl)/(F.sh-F.sl),'pos_in_rth':(c-F.rl)/(F.rh-F.rl),'range_used':(F.sh-F.sl)/A,
 'volreg':F.atr60/F.atr390,'atr14_rel':F.atr14/A,'mod':F['mod'],
 'dist_ph':(c-F.ph)/A,'dist_pl':(c-F.pl)/A,'dist_pcl':(c-F.pcl)/A,
 'dow':F.ts.dt.dayofweek,
})
X['yr']=F.ts.dt.year; is_=(F.ts<'2024-01-01').values
k='0.1'
base_L=L[f'L{k}'][is_].mean(); base_S=L[f'S{k}'][is_].mean()
print(f"2023 base long {base_L:.3f} short {base_S:.3f}")
rows=[]
for col in X.columns:
    if col=='yr': continue
    x=X[col][is_]
    try: b=pd.qcut(x,10,labels=False,duplicates='drop')
    except: continue
    gL=L[f'L{k}'][is_].groupby(b).mean(); gS=L[f'S{k}'][is_].groupby(b).mean()
    rows.append((col,gL.max(),gL.idxmax(),gS.max(),gS.idxmax(),gL.min(),gS.min()))
R=pd.DataFrame(rows,columns=['feat','bestL','binL','bestS','binS','worstL','worstS']).round(3)
print(R.sort_values('bestL',ascending=False).to_string())
