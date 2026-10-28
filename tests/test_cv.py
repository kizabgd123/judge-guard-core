"""
Unit tests for Cross-Validation and Metric Engine (src/cv.py).
"""

import pytest
import numpy as np
import pandas as pd

from src.cv import get_cv_folds, evaluate_auc

def test_get_cv_folds():
    n_samples = 100
    y = pd.Series([0] * 60 + [1] * 40)
    X = pd.DataFrame({"feat": np.random.randn(n_samples)})

    folds = list(get_cv_folds(X, y, n_splits=5, seed=42))
    assert len(folds) == 5

    seen_val_indices = []
    for train_idx, val_idx in folds:
        # No overlap within fold
        assert len(set(train_idx).intersection(set(val_idx))) == 0
        assert len(train_idx) + len(val_idx) == n_samples
        seen_val_indices.extend(val_idx)

    # Every index validated exactly once
    assert sorted(seen_val_indices) == list(range(n_samples))

def test_evaluate_auc():
    y_true = np.array([0, 0, 1, 1])
    y_pred_perfect = np.array([0.1, 0.2, 0.8, 0.9])
    y_pred_random = np.array([0.5, 0.5, 0.5, 0.5])

    assert evaluate_auc(y_true, y_pred_perfect) == 1.0
    assert evaluate_auc(y_true, y_pred_random) == 0.5
