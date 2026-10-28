"""
Unit and integration tests for Kaggle S6E10 pipeline.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score

from src.config import cfg
from src.data_loader import load_data, reduce_mem_usage
from src.preprocessing import FeatureEngineer
from src.models.baseline import get_model, train_kfold_model
from src.models.ensemble import rank_average, optimize_blend

def test_config():
    assert cfg.TARGET_COL == "satisfaction"
    assert cfg.ID_COL == "id"
    assert cfg.EVAL_METRIC == "roc_auc"
    assert cfg.RAW_DATA_DIR.exists()
    assert cfg.TRAIN_PATH.exists()
    assert cfg.TEST_PATH.exists()

def test_data_loader():
    train, test, sub = load_data(nrows=100)
    assert len(train) == 100
    assert len(test) == 100
    assert len(sub) == 100
    assert cfg.TARGET_COL in train.columns
    assert set(train[cfg.TARGET_COL].unique()).issubset({0, 1})
    assert cfg.ID_COL in test.columns

def test_feature_engineer():
    train, test, _ = load_data(nrows=150)
    fe = FeatureEngineer()
    tr_eng, te_eng = fe.fit_transform(train, test)

    expected_new_cols = [
        'Total_Delay', 'Delay_Diff', 'Is_Delayed', 'Severe_Delay',
        'Survey_Mean', 'Survey_Std', 'Survey_Sum', 'Survey_Pain_Points',
        'Comfort_Score', 'Digital_Score', 'Service_Score',
        'Class_TravelType', 'Customer_Class'
    ]

    for col in expected_new_cols:
        assert col in tr_eng.columns, f"Missing feature: {col}"
        assert col in te_eng.columns, f"Missing feature in test: {col}"

    assert tr_eng['Arrival Delay in Minutes'].isnull().sum() == 0
    assert te_eng['Arrival Delay in Minutes'].isnull().sum() == 0
    assert len(fe.feature_names) > 20

def test_model_training_fast():
    train, test, _ = load_data(nrows=200)
    fe = FeatureEngineer()
    tr_eng, te_eng = fe.fit_transform(train, test)

    X = tr_eng[fe.feature_names]
    y = tr_eng[cfg.TARGET_COL]
    X_test = te_eng[fe.feature_names]

    fast_params = {
        "n_estimators": 10,
        "learning_rate": 0.1,
        "max_depth": 3,
        "num_leaves": 7,
        "verbose": -1
    }

    oof, test_preds, cv_score, fold_scores = train_kfold_model(
        model_name="lgb",
        X=X,
        y=y,
        X_test=X_test,
        n_splits=2,
        params=fast_params,
        verbose=False
    )

    assert len(oof) == 200
    assert len(test_preds) == 200
    assert 0.0 <= cv_score <= 1.0
    assert len(fold_scores) == 2
    assert (oof >= 0.0).all() and (oof <= 1.0).all()
    assert (test_preds >= 0.0).all() and (test_preds <= 1.0).all()

def test_ensemble_methods():
    np.random.seed(42)
    y_true = np.random.randint(0, 2, size=100)
    m1 = np.clip(y_true * 0.7 + np.random.normal(0, 0.2, size=100), 0, 1)
    m2 = np.clip(y_true * 0.65 + np.random.normal(0, 0.2, size=100), 0, 1)

    # Rank average
    rank_res = rank_average([m1, m2])
    assert len(rank_res) == 100
    assert (rank_res >= 0.0).all() and (rank_res <= 1.0).all()

    # Blend
    blend_oof, blend_test, weights, auc = optimize_blend([m1, m2], y_true, [m1, m2])
    assert len(blend_oof) == 100
    assert len(blend_test) == 100
    assert len(weights) == 2
    assert np.isclose(np.sum(weights), 1.0)
    assert 0.5 <= auc <= 1.0
