"""
Ensembling techniques for ROC-AUC optimization.
Includes Rank Averaging and Scipy-optimized Soft Blending.
"""

import numpy as np
from scipy.stats import rankdata
from scipy.optimize import minimize
from sklearn.metrics import roc_auc_score
from typing import List, Tuple, Optional

def rank_average(preds_list: List[np.ndarray]) -> np.ndarray:
    """
    Computes normalized rank average of multiple probability prediction arrays.
    ROC-AUC is rank-based, so rank averaging avoids calibration scale mismatches.
    """
    ranked_preds = [rankdata(p) / len(p) for p in preds_list]
    return np.mean(ranked_preds, axis=0)

def optimize_blend(
    oof_list: List[np.ndarray],
    y_true: np.ndarray,
    test_list: Optional[List[np.ndarray]] = None
) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray, float]:
    """
    Finds optimal convex combination of model predictions to maximize ROC-AUC.
    """
    n_models = len(oof_list)
    initial_weights = np.ones(n_models) / n_models

    def loss(weights):
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        blend_oof = sum(w * oof for w, oof in zip(weights, oof_list))
        # Negative ROC-AUC for minimization
        return -roc_auc_score(y_true, blend_oof)

    bounds = [(0, 1) for _ in range(n_models)]
    constraints = ({'type': 'eq', 'fun': lambda w: 1 - sum(w)})

    res = minimize(
        loss,
        initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    opt_weights = res.x / np.sum(res.x)
    blend_oof = sum(w * oof for w, oof in zip(opt_weights, oof_list))
    best_auc = roc_auc_score(y_true, blend_oof)

    blend_test = None
    if test_list is not None:
        blend_test = sum(w * test for w, test in zip(opt_weights, test_list))

    return blend_oof, blend_test, opt_weights, best_auc
