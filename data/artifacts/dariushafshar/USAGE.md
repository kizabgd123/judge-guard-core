# Using the original data the measured way

Fifteen lines: merge the lookup tables, add the original-only model's two features (the first ten lines, the same as in `README.md`), fit LightGBM, write a submission. It is written for a Kaggle notebook that has this dataset and the S6E10 competition attached.

```python
import glob, os, sys, pandas as pd
find = lambda name: glob.glob(f"/kaggle/input/**/{name}", recursive=True)[0]
D = os.path.dirname(find("lookup_long.csv"))                       # this dataset
sys.path.append(D); from original_model import score                # the original-only model
L = pd.read_csv(f"{D}/lookup_long.csv", dtype={"value": str}, keep_default_na=False)
train, test = (pd.read_csv(find(f"playground-series-s6e10/{s}.csv")) for s in ("train", "test"))
for df in (train, test):
    for f, t in L[L.feature.isin(df.columns)].groupby("feature"):   # 21 lookup columns
        df["orig_rate__" + f] = df[f].astype(str).fillna("nan").map(dict(zip(t.value, t.rate)))
    df[["ogp_xgb_d8", "ogp_lgb"]] = score(df).to_numpy()             # 2 original-model logits
import lightgbm as lgb
cat = {c: "category" for c in ["Gender", "Customer Type", "Type of Travel", "Class"]}
X, Xt = train.drop(columns=["id", "satisfaction"]).astype(cat), test.drop(columns=["id"]).astype(cat)
m = lgb.LGBMClassifier(learning_rate=0.05, num_leaves=63, n_estimators=500, verbose=-1).fit(X, train.satisfaction)
pd.DataFrame({"id": test.id, "satisfaction": m.predict_proba(Xt)[:, 1]}).to_csv("submission.csv", index=False)
```

**What each step is worth, measured** (paired 5-fold deltas on a frozen partition, competition rows only; links in `README.md`):

* step 1, lookup columns: **+0.000927** AUC, 5/5 folds, on a plain LightGBM (*S6E10 | Original Data: Rows vs Lookup*);
* step 2, original model as a feature: **+0.000287**, 5/5 folds, on a LightGBM with counts and route profile (*S6E10: 6 Ideas Measured, 4 Pay, 2 Don't*);
* appending the original rows instead: -0.000252, 0/5 folds.

They were measured on different baselines; do not add them up.

## Notes

* **Validate on competition rows only.** The lookup tables and the model read only the original's labels, so you can build them once for every row; they leak nothing across your folds.
* **Smoothing.** Swap `t.rate` for `t.rate_smoothed` (m = 20, toward the original's satisfied share) or rebuild your own from `n_rows` and `n_satisfied`.
* **The combination key.** `lookup_long.csv` also holds `Type of Travel|Class|Customer Type`. The loop above skips it because it is not a column of `train.csv`; to add it, build `key = df["Type of Travel"].astype(str) + "|" + df["Class"].astype(str) + "|" + df["Customer Type"].astype(str)` and map it the same way.
* **Wide format.** `lookup_wide.csv` is the same `rate` column for every feature, one row per value: `W = pd.read_csv(path, dtype={"value": str}, keep_default_na=False, na_values=[""]).set_index("value")`, then `df["orig_rate__" + f] = df[f].astype(str).fillna("nan").map(W["orig_rate__" + f])`.
* **The model.** `score(df)` returns `ogp_xgb_d8` and `ogp_lgb` (logits) with `df`'s index. It needs the 21 feature columns and nothing else. Use them as features, not as `init_score` (-0.006306 in the same ladder).
* **Adding the original rows too.** Run the same two steps on `original_aligned.csv`, set `is_original` to 1 there and 0 on `train.csv` and `test.csv`, and append the rows to every training fold only. Measured: +0.001029 with the lookup columns, against +0.000927 for the lookup columns alone.

Data: Arseniy Shutko's [Airline Satisfaction Data](https://www.kaggle.com/datasets/arseniyshutko/binary-aviation-satisfaction-129k), CC0-1.0.
