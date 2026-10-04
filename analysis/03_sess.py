import pandas as pd, numpy as np
df=pd.read_pickle('nq.pkl')
m=df.ts.dt.hour*60+df.ts.dt.minute
df['mod']=m
# bars close-time labelled; session day: bars after 17:00 belong to next date
d=df.ts.dt.normalize()
df['sd']=np.where(m>17*60, d+pd.Timedelta(days=1), d)
df['sd']=pd.to_datetime(df['sd'])
# Sunday evening -> Monday handled: Sunday 18:01 +1 = Monday. Friday 18:01 doesn't exist.
# sub-sessions by bar CLOSE time (bar covers mod-1..mod)
def lab(x):
    if x>17*60 or x<=2*60: return 'ASIA'     # 18:00-02:00
    if x<=8*60+30: return 'LON'              # 02:00-08:30
    if x<=9*60+30: return 'PRE'              # 08:30-09:30
    if x<=16*60: return 'RTH'                # 09:30-16:00
    return 'POST'                             # 16:00-17:00
lut=np.array([lab(i) for i in range(1440)]); df['ss']=lut[m]
df.to_pickle('nq2.pkl')
print(df.groupby('ss').size()); print("sessions:", df.sd.nunique())
