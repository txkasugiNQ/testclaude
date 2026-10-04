"""Second research round: event library + level library (all causal)."""
from families import *
key=df.sd.values
def sess_level(mask,valid_from_mod,fn='max'):
    src=np.where(mask,h if fn=='max' else l,np.nan)
    s=pd.Series(src).groupby(key)
    v=(s.transform('max') if fn=='max' else s.transform('min')).values
    return np.where(m>valid_from_mod,v,np.nan) if valid_from_mod is not None else v
# overnight (18:00-09:30), Asia (18:00-02:00), London (02:00-08:30); valid during RTH only (after 09:30)
ovn=(m>1020)|(m<=570); asia=(m>1020)|(m<=120); lon=(m>120)&(m<=510)
ONH=np.where(rth,sess_level(ovn,None,'max'),np.nan); ONL=np.where(rth,sess_level(ovn,None,'min'),np.nan)
ASH=np.where(rth,sess_level(asia,None,'max'),np.nan); ASL=np.where(rth,sess_level(asia,None,'min'),np.nan)
LOH=np.where(rth,sess_level(lon,None,'max'),np.nan); LOL=np.where(rth,sess_level(lon,None,'min'),np.nan)
# prior week (by session date) H/L
_D=df.groupby('sd').agg(H=('h','max'),L=('l','min'))
_wk=_D.index.to_period('W-FRI'); _W=_D.groupby(_wk).agg(H=('H','max'),L=('L','min')).shift()
PWH=df.sd.map(pd.Series(_W.H.reindex(_wk).values,index=_D.index)).values; PWL=df.sd.map(pd.Series(_W.L.reindex(_wk).values,index=_D.index)).values
LEV={'PDH':ph,'PDL':pl,'ONH':ONH,'ONL':ONL,'ASH':ASH,'ASL':ASL,'LOH':LOH,'LOL':LOL,'IBH':orH[60],'IBL':orL[60],'OR15H':orH[15],'OR15L':orL[15],'OR30H':orH[30],'OR30L':orL[30],'PWH':PWH,'PWL':PWL}
UPPER=['PDH','ONH','ASH','LOH','IBH','OR15H','OR30H','PWH']
LOWER=['PDL','ONL','ASL','LOL','IBL','OR15L','OR30L','PWL']
def first_cross(level,d,W):
    """first close beyond level per day (d=+1 above). Requires previous close on the other side."""
    if d>0: cond=W&~np.isnan(level)&(c>level)&(prev(c)<=level)
    else:   cond=W&~np.isnan(level)&(c<level)&(prev(c)>=level)
    return once_per_day(cond)
