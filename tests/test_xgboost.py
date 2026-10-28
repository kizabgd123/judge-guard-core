"""
Unit tests for XGBoost 5-Fold Trainer (src/models/xgboost_model.py).
"""

import pytest
import numpy as np
import pandas as pd

from src.models.xgboost_model import train_xgboost_kfold

def test_train_xgboost_kfold_fast():
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        "feat1": np.random.randn(n),
        "feat2": np.random.randint(1, 6, size=n),
        "feat3": np.random.choice([0, 1], size=n)
    })
    y = pd.Series(np.random.choice([0, 1], size=n))
    X_test = pd.DataFrame({
        "feat1": np.random.randn(30),
        "feat2": np.random.randint(1, 6, size=30),
        "feat3": np.random.choice([0, 1], size=30)
    })

    fast_params = {
        "n_estimators": 10,
        "learning_rate": 0.1,
        "max_depth": 3,
        "tree_method": "hist"
    }

    oof_preds, test_preds, oof_auc, fold_aucs = train_xgboost_kfold(
        X, y, X_test, n_splits=3, params=fast_params, early_stopping_rounds=5, verbose=False
    )

    assert len(oof_preds) == n
    assert len(test_preds) == 30
    assert len(fold_aucs) == 3
    assert 0.0 <= oof_auc <= 1.0
    assert (oof_preds >= 0.0).all() and (oof_preds <= 1.0).all()
    assert (test_preds >= 0.0).all() and (test_preds <= 1.0).all()
