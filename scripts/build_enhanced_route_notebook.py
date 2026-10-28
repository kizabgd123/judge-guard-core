import json
import os

nb = {
    "cells": [],
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": []},
        "gpuClass": "standard",
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.10.12"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 0
}

def add_md(text):
    nb["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    })

def add_code(text):
    nb["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.strip().split("\n")]
    })

# Cell 0: Header
add_md("""# ✈️ S6E10 Enhanced Route Tri-GBDT Pipeline (v3)
### Kaggle Playground Series Season 6 Episode 10: Airline Passenger Satisfaction
**Evaluation Metric:** Area Under the ROC Curve (ROC-AUC)

## Architectural Advancements in Version 3:
1. **Full 13 Survey Dimensions:** Added `Baggage handling` to the survey feature set.
2. **CTGAN Structural Zero Flags:** Explicit binary indicators (`{col}_is_zero`) capturing N/A survey services in synthetic data, plus interaction flags (`wifi_0_booking_0`, `food_0_entertainment_0`, `zero_survey_count`).
3. **Nonlinear Delay Recovery Dynamics:** `log_dep_delay`, `log_arr_delay`, `delay_recovery` (Arrival - Departure), `has_no_delay`, `has_extreme_delay`, and `delay_per_distance`.
4. **Leak-Free In-Fold Bayesian Target Encoding:** Route-ID M-estimate smoothing ($m=20$) computed strictly inside each 5-fold cross-validation split on `Flight Distance`.
5. **High-Resolution Tri-GBDT Stack:**
   - **LightGBM:** `num_leaves=63`, `learning_rate=0.03`, `subsample=0.8`, `colsample_bytree=0.8`, `n_estimators=2500`
   - **CatBoost:** `depth=7`, `learning_rate=0.04`, `iterations=2500`, GPU accelerated
   - **XGBoost:** `max_depth=7`, `learning_rate=0.03`, `max_bin=512`, `tree_method='hist'`, `n_estimators=2500`
6. **Nelder-Mead Rank Percentile Ensembling:** Softmax-constrained optimization on Out-Of-Fold ranks directly maximizing ROC-AUC.""")

# Cell 1: Environment & Setup
add_code("""import os
import gc
import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from scipy.optimize import minimize
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OrdinalEncoder

import lightgbm as lgb
from catboost import CatBoostClassifier
import xgboost as xgb

warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

print(f"NumPy version : {np.__version__}")
print(f"Pandas version: {pd.__version__}")
print(f"LightGBM ver  : {lgb.__version__}")
print(f"XGBoost ver   : {xgb.__version__}")
""")

# Cell 2: Data Discovery
add_md("""## 1. Dynamic Dataset Discovery & Loading
Automatically discovers training and test sets across local and Kaggle paths.""")

add_code("""def find_file(filename):
    for root in ["/kaggle/input", "./data", "../data", "./datasets", "../datasets", "."]:
        for path in Path(root).rglob(filename):
            return str(path)
    return None

train_path = find_file("train.csv")
test_path = find_file("test.csv")
sub_path = find_file("sample_submission.csv")

print(f"Resolved Train Path : {train_path}")
print(f"Resolved Test Path  : {test_path}")

assert train_path is not None and test_path is not None, "Data files not found!"

train_raw = pd.read_csv(train_path)
test_raw = pd.read_csv(test_path)
sub = pd.read_csv(sub_path)

print(f"Train dataset shape: {train_raw.shape}")
print(f"Test dataset shape : {test_raw.shape}")
""")

# Cell 3: Feature Engineering
add_md("""## 2. Comprehensive Feature Engineering
Includes all 13 survey dimensions, CTGAN zero flags, non-linear delay features, and route frequency.""")

add_code("""SURVEY_FEATURES = [
    "Inflight wifi service", "Departure/Arrival time convenient", "Ease of Online booking",
    "Gate location", "Food and drink", "Online boarding", "Seat comfort",
    "Inflight entertainment", "On-board service", "Leg room service", "Baggage handling",
    "Checkin service", "Cleanliness"
]

def engineer_features(train_df, test_df):
    tr = train_df.copy()
    te = test_df.copy()

    # Route frequency count (leak-free across full distance spectrum)
    full_dist = pd.concat([tr["Flight Distance"], te["Flight Distance"]], axis=0)
    dist_freq = full_dist.value_counts().to_dict()

    for df in [tr, te]:
        # 1. Missing arrival delay handling & nonlinear dynamics
        df["is_missing_arrival_delay"] = df["Arrival Delay in Minutes"].isnull().astype(np.int8)
        df["Arrival Delay in Minutes"] = df["Arrival Delay in Minutes"].fillna(df["Departure Delay in Minutes"])
        
        dep_delay = df["Departure Delay in Minutes"]
        arr_delay = df["Arrival Delay in Minutes"]
        
        df["total_delay"] = dep_delay + arr_delay
        df["delay_recovery"] = arr_delay - dep_delay
        df["delay_per_distance"] = df["total_delay"] / (df["Flight Distance"] + 1.0)
        df["is_delayed"] = (df["total_delay"] > 0).astype(np.int8)
        df["has_no_delay"] = ((dep_delay == 0) & (arr_delay == 0)).astype(np.int8)
        df["has_extreme_delay"] = (dep_delay > 120).astype(np.int8)
        df["log_dep_delay"] = np.log1p(np.maximum(dep_delay, 0)).astype(np.float32)
        df["log_arr_delay"] = np.log1p(np.maximum(arr_delay, 0)).astype(np.float32)

        # 2. Domain satisfaction indices
        df["inflight_comfort_index"] = df[["Seat comfort", "Inflight entertainment", "Cleanliness", "Food and drink"]].mean(axis=1)
        df["digital_exp_index"] = df[["Inflight wifi service", "Ease of Online booking"]].mean(axis=1)
        df["service_quality_index"] = df[["On-board service", "Leg room service", "Checkin service", "Baggage handling"]].mean(axis=1)
        df["ground_service_index"] = df[["Checkin service", "Gate location", "Departure/Arrival time convenient"]].mean(axis=1)

        # 3. Rating statistics & Asymmetric Pain Points
        s_slice = df[SURVEY_FEATURES]
        df["ratings_sum"] = s_slice.sum(axis=1)
        df["ratings_mean"] = s_slice.mean(axis=1)
        df["ratings_std"] = s_slice.std(axis=1).fillna(0.0)
        df["ratings_min"] = s_slice.min(axis=1)
        df["ratings_max"] = s_slice.max(axis=1)
        df["low_rating_count"] = (s_slice <= 2).sum(axis=1)
        df["high_rating_count"] = (s_slice >= 4).sum(axis=1)

        # 4. CTGAN Structural Zero Flags (N/A Survey Ratings)
        for c in SURVEY_FEATURES:
            df[f"{c}_is_zero"] = (df[c] == 0).astype(np.int8)
        df["wifi_0_booking_0"] = ((df["Inflight wifi service"] == 0) & (df["Ease of Online booking"] == 0)).astype(np.int8)
        df["food_0_entertainment_0"] = ((df["Food and drink"] == 0) & (df["Inflight entertainment"] == 0)).astype(np.int8)
        df["zero_survey_count"] = (s_slice == 0).sum(axis=1).astype(np.int8)

        # 5. Cross categoricals
        df["class_travel_type"] = df["Class"].astype(str) + "_" + df["Type of Travel"].astype(str)
        df["customer_class"] = df["Customer Type"].astype(str) + "_" + df["Class"].astype(str)

        # 6. Route frequency mapping
        df["route_frequency"] = df["Flight Distance"].map(dist_freq)

    # Encode categoricals
    cat_cols = ["Gender", "Customer Type", "Type of Travel", "Class", "class_travel_type", "customer_class"]
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    tr[cat_cols] = enc.fit_transform(tr[cat_cols].astype(str))
    te[cat_cols] = enc.transform(te[cat_cols].astype(str))

    return tr, te

train_feat, test_feat = engineer_features(train_raw, test_raw)
print(f"Feature engineering completed. Enhanced feature count: {train_feat.shape[1]}")
""")

# Cell 4: Bayesian In-Fold Target Encoding
add_md("""## 3. Zero-Leakage In-Fold Bayesian Target Encoding
Calculates Bayesian smoothed target encoding ($m=20$) for `Flight Distance` strictly inside each fold.""")

add_code("""N_SPLITS = 5
skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
folds = list(skf.split(train_feat, train_feat["satisfaction"]))

def compute_route_target_encoding(train_df, test_df, folds, smoothing=20.0):
    tr = train_df.copy()
    te = test_df.copy()
    
    tr["route_target_enc"] = 0.0
    te["route_target_enc"] = 0.0
    
    for fold, (t_idx, v_idx) in enumerate(folds):
        f_train = tr.iloc[t_idx]
        f_val = tr.iloc[v_idx]
        
        global_mean = f_train["satisfaction"].mean()
        stats = f_train.groupby("Flight Distance")["satisfaction"].agg(["count", "mean"])
        
        # Bayesian M-estimate smoothing formula
        smooth_enc = (stats["count"] * stats["mean"] + smoothing * global_mean) / (stats["count"] + smoothing)
        
        tr.iloc[v_idx, tr.columns.get_loc("route_target_enc")] = f_val["Flight Distance"].map(smooth_enc).fillna(global_mean).values
        te["route_target_enc"] += te["Flight Distance"].map(smooth_enc).fillna(global_mean).values / len(folds)
        
    return tr, te

train_final, test_final = compute_route_target_encoding(train_feat, test_feat, folds, smoothing=20.0)

ignore_cols = ["id", "satisfaction"]
feature_cols = [c for c in train_final.columns if c not in ignore_cols]
print(f"Total features entering model training: {len(feature_cols)}")
print("Sample feature columns:", feature_cols[:15], "...")
""")

# Cell 5: Model Training
add_md("""## 4. 5-Fold Stratified Tri-GBDT Model Training
LightGBM + CatBoost (iterations 2500, GPU) + High-Bin XGBoost (max_bin=512, hist).""")

add_code("""X = train_final[feature_cols]
y = train_final["satisfaction"]
X_test = test_final[feature_cols]

oof_preds = {}
test_preds = {}

# 1. LightGBM
print("=" * 60)
print("🚀 [1/3] Training 5-Fold LightGBM...")
lgb_oof = np.zeros(len(X), dtype=np.float32)
lgb_test = np.zeros(len(X_test), dtype=np.float32)

for fold, (t_idx, v_idx) in enumerate(folds):
    model = lgb.LGBMClassifier(
        objective="binary", metric="auc", learning_rate=0.03, num_leaves=63,
        max_depth=-1, min_child_samples=50, subsample=0.8, colsample_bytree=0.8,
        n_estimators=2500, random_state=42, n_jobs=-1, verbose=-1
    )
    model.fit(
        X.iloc[t_idx], y.iloc[t_idx],
        eval_set=[(X.iloc[v_idx], y.iloc[v_idx])],
        callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)]
    )
    val_pred = model.predict_proba(X.iloc[v_idx])[:, 1]
    lgb_oof[v_idx] = val_pred
    lgb_test += model.predict_proba(X_test)[:, 1] / N_SPLITS
    print(f"  LGB Fold {fold + 1} ROC-AUC: {roc_auc_score(y.iloc[v_idx], val_pred):.5f}")

lgb_auc = roc_auc_score(y, lgb_oof)
print(f"⭐ LightGBM Overall OOF ROC-AUC: {lgb_auc:.5f}")
oof_preds["LGBM"] = lgb_oof
test_preds["LGBM"] = lgb_test

# 2. CatBoost
print("\\n" + "=" * 60)
print("🚀 [2/3] Training 5-Fold CatBoost...")
cat_oof = np.zeros(len(X), dtype=np.float32)
cat_test = np.zeros(len(X_test), dtype=np.float32)

for fold, (t_idx, v_idx) in enumerate(folds):
    model = CatBoostClassifier(
        iterations=2500, learning_rate=0.04, depth=7, eval_metric="AUC",
        random_seed=42, thread_count=-1, verbose=False
    )
    model.fit(
        X.iloc[t_idx], y.iloc[t_idx],
        eval_set=(X.iloc[v_idx], y.iloc[v_idx]),
        early_stopping_rounds=100, verbose=False
    )
    val_pred = model.predict_proba(X.iloc[v_idx])[:, 1]
    cat_oof[v_idx] = val_pred
    cat_test += model.predict_proba(X_test)[:, 1] / N_SPLITS
    print(f"  CAT Fold {fold + 1} ROC-AUC: {roc_auc_score(y.iloc[v_idx], val_pred):.5f}")

cat_auc = roc_auc_score(y, cat_oof)
print(f"⭐ CatBoost Overall OOF ROC-AUC: {cat_auc:.5f}")
oof_preds["CatBoost"] = cat_oof
test_preds["CatBoost"] = cat_test

# 3. High-Bin XGBoost
print("\\n" + "=" * 60)
print("🚀 [3/3] Training 5-Fold High-Bin XGBoost (max_bin=512)...")
xgb_oof = np.zeros(len(X), dtype=np.float32)
xgb_test = np.zeros(len(X_test), dtype=np.float32)

for fold, (t_idx, v_idx) in enumerate(folds):
    model = xgb.XGBClassifier(
        learning_rate=0.03, max_depth=7, subsample=0.8, colsample_bytree=0.8,
        eval_metric="auc", tree_method="hist", max_bin=512, n_estimators=2500,
        early_stopping_rounds=100, random_state=42, n_jobs=-1
    )
    model.fit(
        X.iloc[t_idx], y.iloc[t_idx],
        eval_set=[(X.iloc[v_idx], y.iloc[v_idx])],
        verbose=False
    )
    val_pred = model.predict_proba(X.iloc[v_idx])[:, 1]
    xgb_oof[v_idx] = val_pred
    xgb_test += model.predict_proba(X_test)[:, 1] / N_SPLITS
    print(f"  XGB Fold {fold + 1} ROC-AUC: {roc_auc_score(y.iloc[v_idx], val_pred):.5f}")

xgb_auc = roc_auc_score(y, xgb_oof)
print(f"⭐ XGBoost Overall OOF ROC-AUC: {xgb_auc:.5f}")
oof_preds["XGBoost"] = xgb_oof
test_preds["XGBoost"] = xgb_test
""")

# Cell 6: Ensembling & Submission Export
add_md("""## 5. Nelder-Mead Rank Percentile Ensembling & Submission Export
Optimizes rank blend weights on Out-Of-Fold predictions and generates final submission.""")

add_code("""def rank_norm(p):
    return (rankdata(p) - 0.5) / len(p)

model_names = ["LGBM", "CatBoost", "XGBoost"]
ranked_oofs = [rank_norm(oof_preds[m]) for m in model_names]

def loss(params):
    exp_p = np.exp(params - np.max(params))
    w = exp_p / np.sum(exp_p)
    blend = sum(wi * oi for wi, oi in zip(w, ranked_oofs))
    return -roc_auc_score(y, blend)

res = minimize(loss, np.zeros(len(model_names)), method="Nelder-Mead", options={"maxiter": 500})
exp_p = np.exp(res.x - np.max(res.x))
opt_w = exp_p / np.sum(exp_p)
blend_auc = -res.fun

print("=" * 60)
print(f"🏆 Optimal Nelder-Mead Rank Ensemble OOF ROC-AUC: {blend_auc:.5f}")
for m, w in zip(model_names, opt_w):
    print(f"  - {m} Weight: {w:.4f} (Individual OOF: {roc_auc_score(y, oof_preds[m]):.5f})")

# Generate test predictions
ranked_tests = [rank_norm(test_preds[m]) for m in model_names]
blend_test = sum(wi * ti for wi, ti in zip(opt_w, ranked_tests))

sub["satisfaction"] = blend_test
sub.to_csv("submission.csv", index=False)
print(f"\\n✅ Successfully generated submission.csv (Rows: {len(sub):,}, Nulls: {sub.isnull().sum().sum()})")

metrics = {
    "lgbm_oof": float(lgb_auc),
    "catboost_oof": float(cat_auc),
    "xgboost_oof": float(xgb_auc),
    "ensemble_blend_oof": float(blend_auc),
    "weights": {m: float(w) for m, w in zip(model_names, opt_w)}
}
with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
print("Saved metrics.json successfully.")
""")

out_path = "kaggle_cloud_v3/s6e10_enhanced_route_ensemble.ipynb"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print(f"Successfully generated notebook: {out_path} with {len(nb['cells'])} cells.")
