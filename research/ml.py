import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
A = pd.read_pickle('scan2.pkl'); B_ = pd.read_pickle('scan3.pkl')
X = A.join(B_.drop(columns=['split','tod','atr']), how='inner', rsuffix='_b')
X = X[X['L1.5'].notna() & X['C1.0'].notna()]
y_cols = ['L1.5','S1.5','L3.0','S3.0','C1.0','C2.0']
feats = [c for c in X.columns if c not in y_cols+['split']]
for tgt in ['L1.5','C1.0','C2.0']:
    d = X[X[tgt]!=0]
    y = (d[tgt]==1).astype(int)
    tr = d.split=='IS'; va = d.split=='VAL'
    clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200, l2_regularization=1.0)
    clf.fit(d.loc[tr, feats], y[tr])
    p = clf.predict_proba(d.loc[va, feats])[:,1]
    pi = clf.predict_proba(d.loc[tr, feats])[:,1]
    auc = roc_auc_score(y[va], p); auci = roc_auc_score(y[tr], pi)
    q = pd.qcut(p, 10, labels=False, duplicates='drop')
    hr = pd.Series(y[va].values).groupby(q).mean()
    print(tgt, f'AUC IS={auci:.3f} VAL={auc:.3f}', 'VAL hit by decile:', ' '.join(f'{v:.2f}' for v in hr))
