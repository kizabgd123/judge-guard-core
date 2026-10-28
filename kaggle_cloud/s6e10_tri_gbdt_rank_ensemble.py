"""
S6E10 Tri-GBDT Rank Ensemble - Cloud Kernel
Trains LightGBM, CatBoost, and XGBoost on Kaggle Cloud GPU with 5-Fold Stratified CV
and Nelder-Mead Rank Percentile Blending.
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import roc_auc_score
from scipy.stats import rankdata
from scipy.optimize import minimize

import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier

warnings.filterwarnings("ignore")

SURVEY_FEATURES = [
    "Inflight wifi service",
    "Departure/Arrival time convenient",
    "Ease of Online booking",
    "Gate location",
    "Food and drink",
    "Online boarding",
    "Seat comfort",
    "Inflight entertainment",
    "On-board service",
    "Leg room service",
    "Checkin service",
    "Cleanliness"
]

def find_data_paths():
    # 1. Recursive search in /kaggle/input
    if os.path.exists("/kaggle/input"):
        for root, dirs, files in os.walk("/kaggle/input"):
            if "train.csv" in files:
                p = Path(root)
                print(f"📂 Found competition dataset at: {p}")
                return p / "train.csv", p / "test.csv", p / "sample_submission.csv"

    # 2. Local fallback paths
    for p in [Path("data/raw"), Path("../data/raw"), Path(".")]:
        if (p / "train.csv").exists():
            print(f"📂 Found competition dataset at: {p.resolve()}")
            return p / "train.csv", p / "test.csv", p / "sample_submission.csv"

    if os.path.exists("/kaggle/input"):
        print("Available in /kaggle/input:", list(os.walk("/kaggle/input")))
    raise FileNotFoundError("Could not locate train.csv and test.csv")

def generate_features(train_df: pd.DataFrame, test_df: pd.DataFrame):
    print("Engineering features...")
    train = train_df.copy()
    test = test_df.copy()

    for df in [train, test]:
        df["is_missing_arrival_delay"] = df["Arrival Delay in Minutes"].isnull().astype(np.int8)
        df["Arrival Delay in Minutes"] = df["Arrival Delay in Minutes"].fillna(df["Departure Delay in Minutes"])
        df["total_delay"] = df["Departure Delay in Minutes"] + df["Arrival Delay in Minutes"]
        df["delay_recovery"] = df["Arrival Delay in Minutes"] - df["Departure Delay in Minutes"]
        df["delay_per_distance"] = df["total_delay"] / (df["Flight Distance"] + 1.0)
        df["is_delayed"] = (df["total_delay"] > 0).astype(np.int8)

        df["inflight_comfort_index"] = df[["Seat comfort", "Inflight entertainment", "Cleanliness", "Food and drink"]].mean(axis=1)
        df["digital_exp_index"] = df[["Inflight wifi service", "Ease of Online booking"]].mean(axis=1)
        df["service_quality_index"] = df[["On-board service", "Leg room service", "Checkin service"]].mean(axis=1)
        df["ground_service_index"] = df[["Checkin service", "Gate location", "Departure/Arrival time convenient"]].mean(axis=1)

        survey_slice = df[SURVEY_FEATURES]
        df["ratings_sum"] = survey_slice.sum(axis=1)
        df["ratings_mean"] = survey_slice.mean(axis=1)
        df["ratings_std"] = survey_slice.std(axis=1).fillna(0.0)
        df["ratings_min"] = survey_slice.min(axis=1)
        df["ratings_max"] = survey_slice.max(axis=1)
        df["low_rating_count"] = (survey_slice <= 2).sum(axis=1)
        df["high_rating_count"] = (survey_slice >= 4).sum(axis=1)

        df["class_travel_type"] = df["Class"].astype(str) + "_" + df["Type of Travel"].astype(str)
        df["customer_class"] = df["Customer Type"].astype(str) + "_" + df["Class"].astype(str)

    cat_cols = ["Gender", "Customer Type", "Type of Travel", "Class", "class_travel_type", "customer_class"]
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    train[cat_cols] = encoder.fit_transform(train[cat_cols].astype(str))
    test[cat_cols] = encoder.transform(test[cat_cols].astype(str))

    feature_names = [c for c in train.columns if c not in ["id", "satisfaction"]]
    return train, test, feature_names

def rank_transform(preds: np.ndarray) -> np.ndarray:
    return (rankdata(preds) - 0.5) / len(preds)

def optimize_blend_weights(oof_preds_list: List[np.ndarray], y_true: np.ndarray):
    ranked_oofs = [rank_transform(p) for p in oof_preds_list]
    n_models = len(oof_preds_list)

    def objective(params: np.ndarray) -> float:
        exp_p = np.exp(params - np.max(params))
        weights = exp_p / np.sum(exp_p)
        blend = sum(w * p for w, p in zip(weights, ranked_oofs))
        return -roc_auc_score(y_true, blend)

    init_params = np.zeros(n_models)
    res = minimize(objective, init_params, method="Nelder-Mead", options={"maxiter": 500})
    exp_p = np.exp(res.x - np.max(res.x))
    optimal_weights = exp_p / np.sum(exp_p)
    best_auc = -res.fun
    return optimal_weights, float(best_auc)

def main():
    print("=" * 60)
    print("Kaggle Cloud GPU Training - S6E10 Tri-GBDT Rank Ensemble")
    print("=" * 60)

    train_path, test_path, sub_path = find_data_paths()
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    sub = pd.read_csv(sub_path)

    # Standardize target to int
    if train_df["satisfaction"].dtype == bool:
        train_df["satisfaction"] = train_df["satisfaction"].astype(int)
    elif train_df["satisfaction"].dtype == object:
        train_df["satisfaction"] = train_df["satisfaction"].apply(lambda x: 1 if str(x).lower() in ["1", "true", "satisfied"] else 0)

    train_feat, test_feat, features = generate_features(train_df, test_df)
    X = train_feat[features]
    y = train_feat["satisfaction"]
    X_test = test_feat[features]

    print(f"Dataset: Train {X.shape}, Test {X_test.shape}")
    n_splits = 5
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    folds = list(skf.split(X, y))

    # 1. LightGBM
    print("\n--- Training LightGBM ---")
    lgb_oof = np.zeros(len(X), dtype=np.float32)
    lgb_test = np.zeros(len(X_test), dtype=np.float32)
    for fold, (t_idx, v_idx) in enumerate(folds):
        m = lgb.LGBMClassifier(
            objective="binary", metric="auc", learning_rate=0.03, num_leaves=63,
            max_depth=-1, min_child_samples=50, subsample=0.8, colsample_bytree=0.8,
            n_estimators=2000, random_state=42, n_jobs=-1, verbose=-1
        )
        m.fit(X.iloc[t_idx], y.iloc[t_idx], eval_set=[(X.iloc[v_idx], y.iloc[v_idx])],
              callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)])
        val_pred = m.predict_proba(X.iloc[v_idx])[:, 1]
        lgb_oof[v_idx] = val_pred
        lgb_test += m.predict_proba(X_test)[:, 1] / n_splits
        print(f"  LGB Fold {fold+1} AUC: {roc_auc_score(y.iloc[v_idx], val_pred):.5f}")
    lgb_auc = roc_auc_score(y, lgb_oof)
    print(f"⭐ LGB Overall OOF AUC: {lgb_auc:.5f}")

    # 2. CatBoost
    print("\n--- Training CatBoost ---")
    cat_oof = np.zeros(len(X), dtype=np.float32)
    cat_test = np.zeros(len(X_test), dtype=np.float32)
    for fold, (t_idx, v_idx) in enumerate(folds):
        m = CatBoostClassifier(
            iterations=2000, learning_rate=0.04, depth=7, eval_metric="AUC",
            random_seed=42, thread_count=-1, verbose=False
        )
        m.fit(X.iloc[t_idx], y.iloc[t_idx], eval_set=(X.iloc[v_idx], y.iloc[v_idx]),
              early_stopping_rounds=100, verbose=False)
        val_pred = m.predict_proba(X.iloc[v_idx])[:, 1]
        cat_oof[v_idx] = val_pred
        cat_test += m.predict_proba(X_test)[:, 1] / n_splits
        print(f"  CAT Fold {fold+1} AUC: {roc_auc_score(y.iloc[v_idx], val_pred):.5f}")
    cat_auc = roc_auc_score(y, cat_oof)
    print(f"⭐ CAT Overall OOF AUC: {cat_auc:.5f}")

    # 3. XGBoost
    print("\n--- Training XGBoost ---")
    xgb_oof = np.zeros(len(X), dtype=np.float32)
    xgb_test = np.zeros(len(X_test), dtype=np.float32)
    for fold, (t_idx, v_idx) in enumerate(folds):
        m = xgb.XGBClassifier(
            learning_rate=0.03, max_depth=7, subsample=0.8, colsample_bytree=0.8,
            eval_metric="auc", tree_method="hist", n_estimators=2000,
            early_stopping_rounds=100, random_state=42, n_jobs=-1
        )
        m.fit(X.iloc[t_idx], y.iloc[t_idx], eval_set=[(X.iloc[v_idx], y.iloc[v_idx])], verbose=False)
        val_pred = m.predict_proba(X.iloc[v_idx])[:, 1]
        xgb_oof[v_idx] = val_pred
        xgb_test += m.predict_proba(X_test)[:, 1] / n_splits
        print(f"  XGB Fold {fold+1} AUC: {roc_auc_score(y.iloc[v_idx], val_pred):.5f}")
    xgb_auc = roc_auc_score(y, xgb_oof)
    print(f"⭐ XGB Overall OOF AUC: {xgb_auc:.5f}")

    # 4. Rank Ensembling
    print("\n--- Optimizing Nelder-Mead Rank Ensemble ---")
    oof_list = [lgb_oof, cat_oof, xgb_oof]
    test_list = [lgb_test, cat_test, xgb_test]
    weights, blend_auc = optimize_blend_weights(oof_list, y.values)
    print(f"⭐ Nelder-Mead Ensemble OOF AUC: {blend_auc:.5f}")
    print(f"  Weights: LGB={weights[0]:.4f}, CAT={weights[1]:.4f}, XGB={weights[2]:.4f}")

    ranked_tests = [rank_transform(p) for p in test_list]
    blend_test = sum(w * p for w, p in zip(weights, ranked_tests))

    # 5. Output
    sub["satisfaction"] = blend_test
    sub.to_csv("submission.csv", index=False)
    print("✅ Successfully generated submission.csv")

    metrics = {
        "lgb_auc": float(lgb_auc),
        "cat_auc": float(cat_auc),
        "xgb_auc": float(xgb_auc),
        "blend_auc": float(blend_auc),
        "weights": [float(w) for w in weights]
    }
    with open("experiment_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    main()
