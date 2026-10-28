"""
Ensemble Engine for Kaggle S6E10.
Implements percentile rank transformation and Nelder-Mead simplex weight optimization.
"""

from typing import List, Tuple
import numpy as np
from scipy.stats import rankdata
from scipy.optimize import minimize

from src.cv import evaluate_auc

def rank_transform(preds: np.ndarray) -> np.ndarray:
    """
    Transforms raw probabilities into uniform percentile ranks in (0, 1].
    Removes scale mismatch across different GBDT model families.
    """
    return (rankdata(preds) - 0.5) / len(preds)

def optimize_blend_weights(
    oof_preds_list: List[np.ndarray],
    y_true: np.ndarray
) -> Tuple[np.ndarray, float]:
    """
    Finds optimal convex combination of model predictions to maximize ROC AUC.
    Uses unconstrained Nelder-Mead with softmax projection.
    """
    ranked_oofs = [rank_transform(p) for p in oof_preds_list]
    n_models = len(oof_preds_list)

    def objective(params: np.ndarray) -> float:
        exp_p = np.exp(params - np.max(params))
        weights = exp_p / np.sum(exp_p)
        blend = sum(w * p for w, p in zip(weights, ranked_oofs))
        return -evaluate_auc(y_true, blend)

    init_params = np.zeros(n_models)
    res = minimize(objective, init_params, method="Nelder-Mead", options={"maxiter": 500})

    exp_p = np.exp(res.x - np.max(res.x))
    optimal_weights = exp_p / np.sum(exp_p)
    best_auc = -res.fun

    return optimal_weights, float(best_auc)

def generate_ensemble_predictions(
    test_preds_list: List[np.ndarray],
    weights: np.ndarray,
    use_ranking: bool = True
) -> np.ndarray:
    """
    Blends multiple test prediction arrays using calibrated weights.
    """
    if use_ranking:
        processed_preds = [rank_transform(p) for p in test_preds_list]
    else:
        processed_preds = test_preds_list

    ensemble_pred = sum(w * p for w, p in zip(weights, processed_preds))
    return ensemble_pred
