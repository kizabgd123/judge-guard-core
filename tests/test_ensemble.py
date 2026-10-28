"""
Unit tests for Ensemble Rank Blending (src/ensemble.py).
"""

import pytest
import numpy as np
from src.ensemble import rank_transform, optimize_blend_weights, generate_ensemble_predictions
from src.cv import evaluate_auc

def test_rank_transform():
    preds = np.array([0.1, 0.5, 0.2, 0.9])
    ranked = rank_transform(preds)

    assert len(ranked) == 4
    assert (ranked >= 0.0).all() and (ranked <= 1.0).all()
    # Monotonicity
    assert ranked[0] < ranked[2] < ranked[1] < ranked[3]

def test_optimize_blend_weights():
    np.random.seed(42)
    n = 200
    y_true = np.random.choice([0, 1], size=n)

    # 3 synthetic model predictions with varying correlation to y_true
    m1 = np.clip(y_true * 0.6 + np.random.normal(0, 0.3, size=n), 0, 1)
    m2 = np.clip(y_true * 0.5 + np.random.normal(0, 0.4, size=n), 0, 1)
    m3 = np.clip(y_true * 0.7 + np.random.normal(0, 0.25, size=n), 0, 1)

    weights, best_auc = optimize_blend_weights([m1, m2, m3], y_true)

    assert len(weights) == 3
    assert np.isclose(np.sum(weights), 1.0)
    assert (weights >= 0.0).all()
    assert best_auc >= evaluate_auc(y_true, m2)

def test_generate_ensemble_predictions():
    m1 = np.array([0.2, 0.8])
    m2 = np.array([0.3, 0.7])
    weights = np.array([0.5, 0.5])

    ens_preds = generate_ensemble_predictions([m1, m2], weights, use_ranking=False)
    assert np.allclose(ens_preds, [0.25, 0.75])

    ens_ranked = generate_ensemble_predictions([m1, m2], weights, use_ranking=True)
    assert len(ens_ranked) == 2
    assert (ens_ranked >= 0.0).all() and (ens_ranked <= 1.0).all()
