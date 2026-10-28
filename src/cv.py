"""
Cross-Validation and Metric Engine for Kaggle S6E10.
Strictly implements StratifiedKFold validation and ROC AUC evaluation.
"""

from typing import List, Tuple, Generator
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

def get_cv_folds(
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    seed: int = 42
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generates deterministic Stratified 5-Fold index pairs.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(X, y))

def evaluate_auc(y_true: np.ndarray, y_pred_prob: np.ndarray) -> float:
    """
    Computes ROC AUC between ground truth labels and predicted probabilities.
    """
    return float(roc_auc_score(y_true, y_pred_prob))
