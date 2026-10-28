# S6E10 Original Data + Lookup Tables + Model

**In ten seconds.** Playground S6E10 was built from Arseniy Shutko's CC0 airline survey (129,880 rows). This dataset turns those rows into features for `train.csv` and `test.csv`, computed from the original file alone:

* **A model fitted on the original rows only** (`original_model.py` and four fitted files). `score(df)` returns two logits, `ogp_xgb_d8` and `ogp_lgb`. Added as two features to a LightGBM that already had value counts and a route profile, they gained **+0.000287 AUC, up in 5/5 folds**. On their own they score 0.95516 and 0.95440 AUC on `train.csv`.
* **The original's satisfied rate for every value of every column** (`lookup_long.csv`). As 21 extra columns on a plain LightGBM: **+0.000927 AUC, up in 5/5 folds**.
* **The rows themselves** (`original_aligned.csv`). Appended as plain extra training rows they measured -0.000252, up in 0/5 folds. With an `is_original` flag, on top of the lookup columns, they measured +0.001029 against +0.000927 for the lookups alone.

These ten lines add all 23 columns to `train` and `test` in a Kaggle notebook that has this dataset and the competition attached:

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
```

No competition row and no competition label is in this dataset.

## Credit

The rows are Arseniy Shutko's upload, [Airline Satisfaction Data](https://www.kaggle.com/datasets/arseniyshutko/binary-aviation-satisfaction-129k), released under CC0-1.0. Every value here, including every number in the lookup tables and the fitted models, comes from that file.

The two uses packaged here were public before I measured them:

* **original target means per value**: 인공저능연구소 (megayak), [S6E10 Honest OOF Stack](https://www.kaggle.com/code/megayak/s6e10-honest-oof-stack), and Arhan canli, [S6E10 | Generator Fingerprints | LGBM CV 0.9610](https://www.kaggle.com/code/arhancanli12/s6e10-generator-fingerprints-lgbm-cv-0-9610);
* **a model fitted on the original only, used as a feature**: goodpjw2008, [S6E10 | Route-ID FE + OG-Model Stack | LB 0.96108](https://www.kaggle.com/code/goodpjw2008/s6e10-route-id-fe-og-model-stack-lb-0-96108) (the XGBoost depth 8 recipe), and Arhan canli (the LightGBM one).

What I added is the packaging, the checks, and the fold by fold measurements below.

## What the measurements say

Every row is a paired comparison on one fold partition, `StratifiedKFold(5, shuffle=True, random_state=42)` on `train.csv`, with only competition rows scored. The delta is the mean of the five per-fold AUC differences.

| how the original enters | added to | mean fold delta (AUC) | folds up | source |
|---|---|---|---|---|
| as extra training rows | LightGBM, 21 raw columns (0.958952) | -0.000252 | 0/5 | [Original Data: Rows vs Lookup](https://www.kaggle.com/code/dariushafshar/s6e10-original-data-rows-vs-lookup-lb-0-95939) |
| as extra rows plus an `is_original` flag | same | +0.000072 | 4/5 | [Original Data: Rows vs Lookup](https://www.kaggle.com/code/dariushafshar/s6e10-original-data-rows-vs-lookup-lb-0-95939) |
| **as per-value lookup columns** (`lookup_long.csv`) | same | **+0.000927** | 5/5 | [Original Data: Rows vs Lookup](https://www.kaggle.com/code/dariushafshar/s6e10-original-data-rows-vs-lookup-lb-0-95939) |
| lookup columns plus flagged rows | same | +0.001029 | 5/5 | [Original Data: Rows vs Lookup](https://www.kaggle.com/code/dariushafshar/s6e10-original-data-rows-vs-lookup-lb-0-95939) |
| **original-only model as a feature** (`original_model.py`) | LightGBM with counts and route profile (0.960411) | **+0.000287** | 5/5 | [S6E10: 6 Ideas Measured, 4 Pay, 2 Don't](https://www.kaggle.com/code/dariushafshar/s6e10-6-ideas-measured-4-pay-2-don-t) |
| original target means, bundled with token keys and fold-safe target encoding | the row above (0.960697) | +0.000298 | 5/5 | [S6E10: 6 Ideas Measured, 4 Pay, 2 Don't](https://www.kaggle.com/code/dariushafshar/s6e10-6-ideas-measured-4-pay-2-don-t) |
| original target means alone (21 lookups + the one combination) | RealMLP that already has the original model (0.961205) | +0.000039 | 5/5 | [RealMLP + Orig. Target Means](https://www.kaggle.com/code/dariushafshar/s6e10-realmlp-orig-target-means-lb-0-96076) |
| boosting from the original model (`init_score`) instead of using it as a feature | LightGBM (0.960990) | -0.006306 | 0/5 | [S6E10: 6 Ideas Measured, 4 Pay, 2 Don't](https://www.kaggle.com/code/dariushafshar/s6e10-6-ideas-measured-4-pay-2-don-t) |

**Lookups and the original model help in every fold. Appended rows do not.** These were measured on different baselines, so do not add the deltas up: a gain on a weak baseline shrinks on a strong one. The same original target means that the ladder measured inside a bundle add +0.000039 to a RealMLP that already has the original model as a feature.

## From features to a submission

Five more lines fit a LightGBM on the ten lines' output and write `submission.csv`. `USAGE.md` has all fifteen with notes on validation.

```python
import lightgbm as lgb
cat = {c: "category" for c in ["Gender", "Customer Type", "Type of Travel", "Class"]}
X, Xt = train.drop(columns=["id", "satisfaction"]).astype(cat), test.drop(columns=["id"]).astype(cat)
m = lgb.LGBMClassifier(learning_rate=0.05, num_leaves=63, n_estimators=500, verbose=-1).fit(X, train.satisfaction)
pd.DataFrame({"id": test.id, "satisfaction": m.predict_proba(Xt)[:, 1]}).to_csv("submission.csv", index=False)
```

These parameters are a plain default, not the measured ones; the measured recipes are in the notebooks linked above.

## Files

| file | rows | what it is |
|---|---|---|
| `original_aligned.csv` | 129,880 | the original rows, aligned to `train.csv` columns, plus `is_original` = 1 (unchanged from version 1) |
| `column_mapping.csv` | 24 | one row per column: source name, name here, what changed (unchanged from version 1) |
| `lookup_long.csv` | 4,933 | one row per (feature, value): rows, satisfied rows, rate, smoothed rate |
| `lookup_wide.csv` | 4,416 | one row per value, one `orig_rate__` column per feature: the measured lookup block, ready to map |
| `original_model.py` |  | fits, loads and scores the original-only model on any frame with `train.csv`'s columns |
| `original_model_xgb_d8.json` |  | fitted XGBoost model (depth 8, 600 trees) |
| `original_model_lgb_seed0.txt`, `_seed1`, `_seed2` |  | fitted LightGBM models (800 rounds each, three seeds) |
| `USAGE.md` |  | the quick start with notes |
| `README.md` |  | this file |

## The lookup tables

For each of the 21 feature columns, and for one combination of three columns, every value the original takes, with:

* `n_rows`: original rows with that value; `n_satisfied`: how many of them are satisfied;
* `rate` = `n_satisfied / n_rows`. This is the column the measured lookup arm used;
* `rate_smoothed` = `(n_satisfied + 20 * 0.434463) / (n_rows + 20)`, where 0.434463 is the original's satisfied share (56,428 of 129,880). It pulls rare values toward the overall share; 2,772 of the 3,821 `Flight Distance` values occur fewer than 20 times. The counts are there so you can choose your own smoothing.

The combination is `Type of Travel|Class|Customer Type` (12 keys), the one combination in the original target means block of our RealMLP. Its keys are the three columns' keys joined with `|`, for example `Business travel|Business|Loyal Customer`.

**Join by value, as text.** `value` is the text pandas gives a column of `train.csv` or `test.csv` read with `pd.read_csv` defaults: integers as `25`, `Arrival Delay in Minutes` (a float column, because it has missing values) as `18.0`, text as written, and missing as `nan`. So the key of a column is `df[col].astype(str).fillna("nan")`; the `.fillna` makes pandas 3, which keeps missing values missing under `astype(str)`, agree with pandas 2. Read the tables with `dtype={"value": str}, keep_default_na=False, na_values=[""]` so that the key `nan` stays text and empty cells stay empty. `value_num` holds the same value as a number for numeric features, for plots or numeric joins.

**Missing values.** The 393 original rows with a missing `Arrival Delay in Minutes` have their own key, `nan` (rate 0.422392). The Rows vs Lookup notebook mapped missing to missing instead, and our RealMLP used the `nan` key; drop that row to get the first behaviour.

**Coverage.** I checked the keys against the competition files. In 20 of the 21 columns, and for the combination, every value in `train.csv` and `test.csv` has a row in the tables, including the missing `Arrival Delay in Minutes` values, which match the `nan` key. The exception is `Flight Distance`: 4 rows of `train.csv` (0.0006%) and 1 of `test.csv` (0.0003%) have a distance the original never takes. Those map to a missing value, which LightGBM and XGBoost route on their own.

**No fold leakage.** The tables read only the original's labels, so they are identical in every fold and can be built once for every competition row. If you also append the original rows, each original row's own label is inside its lookup value; the measured "lookup columns plus flagged rows" arm did exactly that.

## The original-only model

`original_model.py` fits two models on the 129,880 original rows and nothing else, and returns two logits for any frame with `train.csv`'s 21 feature columns:

* `ogp_xgb_d8`: XGBoost, `max_depth` 8, 600 trees, learning rate 0.05, subsample 0.8, `colsample_bytree` 0.5, `hist`, seed 0;
* `ogp_lgb`: LightGBM raw score, mean of seeds 0, 1 and 2, 800 rounds each, learning rate 0.03, 63 leaves, `min_child_samples` 20, feature and bagging fraction 0.8.

The four text columns become integer codes in sorted level order, and the model's input order is fixed in the script. These are the exact settings of the measured ladder rung (+0.000287, 5/5 folds). Scored on `train.csv`, the shipped files give AUC 0.95516 (`ogp_xgb_d8`) and 0.95440 (`ogp_lgb`) on their own; the ladder's own fit of the same recipe on Kaggle printed 0.95506 and 0.95440. Use the outputs as features: boosting from them as `init_score` cost -0.006306 in the same ladder.

The fitted files were written by xgboost 3.3.0 and lightgbm 4.7.0. `score()` loads them; if your versions cannot read them, it re-fits the same recipe from `original_aligned.csv` in memory and says so (about 65 seconds on a 10-core machine). On the original rows themselves, the loaded files and a fresh re-fit give identical logits.

**Why there are no predictions on `train.csv` or `test.csv` here.** My OOF library ships predictions keyed to competition rows, and that is the right place for them. This dataset's rule is different: every value in it is computed from the CC0 original, so it carries no competition data and stays valid whatever the competition files are. Scoring takes a call to `score()`.

## `original_aligned.csv` (version 1, unchanged)

* All 129,880 source rows, in source order, none removed. `train.csv`'s columns in `train.csv`'s order, plus `is_original` = 1. `id` is -(k + 1) for the k-th source row, so ids run from -1 to -129,880 and never collide with a competition id.
* All 22 source columns kept their names; `satisfaction` is True/False in both files; every text level already has `train.csv`'s spelling. `column_mapping.csv` records this per column.
* 0.434463 of rows are satisfied (56,428 of 129,880).
* The two delay columns are minutes (the source page's column table calls them ratings). `Arrival Delay in Minutes` has 393 missing values, kept as missing.
* 13 columns are service ratings from 0 to 5. In 12 of them 0 means not rated, per the source page; `Baggage handling` runs from 1 to 5.

**Validation.** Build folds on competition rows only. If you append original rows, add them to every training fold and never score them: a CV score that includes them measures fit to the original, not to the leaderboard's rows.

## Column dictionary

**`lookup_long.csv`**

| column | meaning |
|---|---|
| `feature` | a `train.csv` column name, or, for the combination, the names `Type of Travel`, `Class` and `Customer Type` joined by a vertical bar |
| `value` | the join key: the value as text, as pandas reads it from `train.csv` (`25`, `18.0`, `Eco Plus`); `nan` = missing |
| `value_num` | the value as a number (numeric features only; empty for text features and for `nan`) |
| `n_rows` | original rows with this value |
| `n_satisfied` | of those, rows with `satisfaction` True |
| `rate` | `n_satisfied / n_rows`, the measured lookup feature |
| `rate_smoothed` | `(n_satisfied + 20 * prior) / (n_rows + 20)`, prior = the original's satisfied share |

**`lookup_wide.csv`**

| column | meaning |
|---|---|
| `value` | the join key, as in `lookup_long.csv` |
| `orig_rate__{feature}` | one column per feature (22): `rate` for that feature at this value; empty where the feature never takes it |

**`original_aligned.csv`**: the 21 feature columns and `satisfaction` as in `train.csv`, plus `id` (negative, see above) and `is_original` (1 on every row).

**`column_mapping.csv`**: `source_column` (name in the source file, empty for added columns), `column_here`, `change`.

## Changes

* **Version 2 (2026-10-08)**: added the lookup tables, the original-only model and its scorer, `USAGE.md`, a column dictionary and a cover image; new title. `original_aligned.csv` and `column_mapping.csv` are byte-identical to version 1.
* **Version 1 (2026-10-01)**: the original rows aligned to `train.csv`.

## Licence

CC0-1.0, the same as the source. Public domain: use it for anything.
