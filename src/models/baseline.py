"""
Cross-validated model training module.
Supports LightGBM, XGBoost, and CatBoost with Stratified K-Fold CV and ROC-AUC evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import lightgbm as lgb
import xgboost as xgb
import catboost as cb

from src.config import cfg

def get_model(model_name: str, params: Optional[Dict[str, Any]] = None):
    """Instantiates a model with default or custom hyper-parameters."""
    model_name = model_name.lower()
    if model_name in ["lgb", "lightgbm"]:
        default_params = {
            "n_estimators": 1500,
            "learning_rate": 0.05,
            "num_leaves": 63,
            "max_depth": 8,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": cfg.RANDOM_SEED,
            "n_jobs": -1,
            "verbose": -1
        }
        if params:
            default_params.update(params)
        return lgb.LGBMClassifier(**default_params)

    elif model_name in ["xgb", "xgboost"]:
        default_params = {
            "n_estimators": 1500,
            "learning_rate": 0.05,
            "max_depth": 6,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "tree_method": "hist",
            "eval_metric": "auc",
            "random_state": cfg.RANDOM_SEED,
            "n_jobs": -1
        }
        if params:
            default_params.update(params)
        return xgb.XGBClassifier(**default_params)

    elif model_name in ["cat", "catboost"]:
        default_params = {
            "iterations": 1500,
            "learning_rate": 0.05,
            "depth": 6,
            "eval_metric": "AUC",
            "random_seed": cfg.RANDOM_SEED,
            "thread_count": -1,
            "verbose": False
        }
        if params:
            default_params.update(params)
        return cb.CatBoostClassifier(**default_params)

    else:
        raise ValueError(f"Unknown model name: {model_name}. Supported: lgb, xgb, cat")

def train_kfold_model(
    model_name: str,
    X: pd.DataFrame,
    y: pd.Series,
    X_test: Optional[pd.DataFrame] = None,
    n_splits: int = cfg.N_FOLDS,
    params: Optional[Dict[str, Any]] = None,
    verbose: bool = True
) -> Tuple[np.ndarray, Optional[np.ndarray], float, List[float]]:
    """
    Trains a model using Stratified K-Fold CV.
    Returns:
      oof_preds: Out-of-fold probability predictions
      test_preds: Average test probability predictions
      cv_auc: Overall OOF ROC-AUC score
      fold_scores: ROC-AUC score for each fold
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=cfg.RANDOM_SEED)
    oof_preds = np.zeros(len(X), dtype=np.float32)
    test_preds = np.zeros(len(X_test), dtype=np.float32) if X_test is not None else None
    fold_scores = []

    if verbose:
        print(f"\n🚀 Training {model_name.upper()} with {n_splits}-Fold Stratified CV...")

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_va, y_va = X.iloc[val_idx], y.iloc[val_idx]

        model = get_model(model_name, params)

        # Fit with early stopping
        if model_name.lower() in ["lgb", "lightgbm"]:
            model.fit(
                X_tr, y_tr,
                eval_set=[(X_va, y_va)],
                eval_metric="auc",
                callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
            )
        elif model_name.lower() in ["xgb", "xgboost"]:
            model.fit(
                X_tr, y_tr,
                eval_set=[(X_va, y_va)],
                verbose=False
            )
        elif model_name.lower() in ["cat", "catboost"]:
            model.fit(
                X_tr, y_tr,
                eval_set=[(X_va, y_va)],
                early_stopping_rounds=50,
                verbose=False
            )

        val_pred = model.predict_proba(X_va)[:, 1]
        oof_preds[val_idx] = val_pred

        fold_auc = roc_auc_score(y_va, val_pred)
        fold_scores.append(fold_auc)

        if verbose:
            print(f"  Fold {fold + 1}/{n_splits} ROC-AUC: {fold_auc:.5f}")

        if X_test is not None:
            test_preds += model.predict_proba(X_test)[:, 1] / n_splits

    cv_auc = roc_auc_score(y, oof_preds)
    if verbose:
        print(f"⭐ {model_name.upper()} Overall OOF ROC-AUC: {cv_auc:.5f} (Std: {np.std(fold_scores):.5f})\n")

    return oof_preds, test_preds, cv_auc, fold_scores
