"""
CatBoost 5-Fold Stratified CV Trainer for Kaggle S6E10.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Tuple, List
from catboost import CatBoostClassifier

from src.cv import get_cv_folds, evaluate_auc

DEFAULT_CATBOOST_PARAMS: Dict[str, Any] = {
    "iterations": 2000,
    "learning_rate": 0.04,
    "depth": 7,
    "eval_metric": "AUC",
    "random_seed": 42,
    "thread_count": -1,
    "verbose": False
}

def train_catboost_kfold(
    X: pd.DataFrame,
    y: pd.Series,
    X_test: Optional[pd.DataFrame] = None,
    n_splits: int = 5,
    params: Optional[Dict[str, Any]] = None,
    early_stopping_rounds: int = 100,
    verbose: bool = True
) -> Tuple[np.ndarray, Optional[np.ndarray], float, List[float]]:
    """
    Trains CatBoost using Stratified K-Fold CV.
    Returns:
        oof_preds, test_preds, oof_auc, fold_aucs
    """
    cat_params = DEFAULT_CATBOOST_PARAMS.copy()
    if params:
        cat_params.update(params)

    folds = get_cv_folds(X, y, n_splits=n_splits, seed=42)
    oof_preds = np.zeros(len(X), dtype=np.float32)
    test_preds = np.zeros(len(X_test), dtype=np.float32) if X_test is not None else None
    fold_aucs: List[float] = []

    if verbose:
        print(f"\n[CatBoost] Training with {n_splits}-Fold Stratified CV...")

    for fold, (train_idx, val_idx) in enumerate(folds):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_va, y_va = X.iloc[val_idx], y.iloc[val_idx]

        model = CatBoostClassifier(**cat_params)
        model.fit(
            X_tr, y_tr,
            eval_set=(X_va, y_va),
            early_stopping_rounds=early_stopping_rounds,
            verbose=False
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
        print(f"⭐ [CatBoost] Overall OOF ROC AUC: {oof_auc:.5f} (Std: {np.std(fold_aucs):.5f})")

    return oof_preds, test_preds, oof_auc, fold_aucs
