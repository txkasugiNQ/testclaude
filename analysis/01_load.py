import pandas as pd, numpy as np
df = pd.read_csv("../Dataset_NQ_1min_2022_2025 (1).csv")
df.columns=['ts','o','h','l','c','v','vr','ve']
df['ts']=pd.to_datetime(df['ts'],format='%m/%d/%Y %H:%M')
df.to_pickle('nq.pkl')
