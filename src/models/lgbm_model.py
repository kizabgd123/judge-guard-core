"""
LightGBM 5-Fold Stratified CV Trainer for Kaggle S6E10.
"""

import warnings
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Tuple, List
import lightgbm as lgb

from src.cv import get_cv_folds, evaluate_auc

warnings.filterwarnings("ignore", category=UserWarning)

DEFAULT_LGBM_PARAMS: Dict[str, Any] = {
    "objective": "binary",
    "metric": "auc",
    "learning_rate": 0.03,
    "num_leaves": 63,
    "max_depth": -1,
    "min_child_samples": 50,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "n_estimators": 2000,
    "random_state": 42,
    "n_jobs": -1,
    "verbose": -1
}

def train_lgbm_kfold(
    X: pd.DataFrame,
    y: pd.Series,
    X_test: Optional[pd.DataFrame] = None,
    n_splits: int = 5,
    params: Optional[Dict[str, Any]] = None,
    early_stopping_rounds: int = 100,
    verbose: bool = True
) -> Tuple[np.ndarray, Optional[np.ndarray], float, List[float]]:
    """
    Trains LightGBM using Stratified K-Fold CV.
    Returns:
        oof_preds, test_preds, oof_auc, fold_aucs
    """
    lgbm_params = DEFAULT_LGBM_PARAMS.copy()
    if params:
        lgbm_params.update(params)

    folds = get_cv_folds(X, y, n_splits=n_splits, seed=42)
    oof_preds = np.zeros(len(X), dtype=np.float32)
    test_preds = np.zeros(len(X_test), dtype=np.float32) if X_test is not None else None
    fold_aucs: List[float] = []

    if verbose:
        print(f"\n[LightGBM] Training with {n_splits}-Fold Stratified CV...")

    for fold, (train_idx, val_idx) in enumerate(folds):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_va, y_va = X.iloc[val_idx], y.iloc[val_idx]

        model = lgb.LGBMClassifier(**lgbm_params)
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_va, y_va)],
            eval_metric="auc",
            callbacks=[lgb.early_stopping(stopping_rounds=early_stopping_rounds, verbose=False)]
        )

        val_pred = model.predict_proba(X_va)[:, 1]
        oof_preds[val_idx] = val_pred
        auc = evaluate_auc(y_va.values, val_pred)
        fold_aucs.append(auc)

        if verbose:
            print(f"  Fold {fold + 1}/{n_splits} ROC AUC: {auc:.5f}")

        if X_test is not None:
            test_preds += model.predict_proba(X_test)[:, 1] / n_splits

    oof_auc = evaluate_auc(y.values, oof_preds)
    if verbose:
        print(f"⭐ [LightGBM] Overall OOF ROC AUC: {oof_auc:.5f} (Std: {np.std(fold_aucs):.5f})")

    return oof_preds, test_preds, oof_auc, fold_aucs
