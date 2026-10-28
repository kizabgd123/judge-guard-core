"""
Unit tests for Feature Engineering Engine (src/features.py).
"""

import pytest
import pandas as pd
import numpy as np

from src.features import generate_features, SURVEY_FEATURES

def create_sample_data(n=20):
    np.random.seed(42)
    data = {
        "id": np.arange(n),
        "Age": np.random.randint(18, 70, size=n),
        "Flight Distance": np.random.randint(100, 3000, size=n),
        "Departure Delay in Minutes": np.random.choice([0, 5, 25, 60], size=n),
        "Arrival Delay in Minutes": np.random.choice([0.0, 10.0, np.nan, 55.0], size=n),
        "Gender": np.random.choice(["Male", "Female"], size=n),
        "Customer Type": np.random.choice(["Loyal Customer", "disloyal Customer"], size=n),
        "Type of Travel": np.random.choice(["Business travel", "Personal Travel"], size=n),
        "Class": np.random.choice(["Eco", "Business", "Eco Plus"], size=n),
        "satisfaction": np.random.choice([0, 1], size=n)
    }
    for col in SURVEY_FEATURES:
        data[col] = np.random.randint(1, 6, size=n)
    return pd.DataFrame(data)

def test_generate_features_columns():
    train_df = create_sample_data(30)
    test_df = create_sample_data(15).drop(columns=["satisfaction"])

    train_feat, test_feat, feature_names = generate_features(train_df, test_df)

    expected_features = [
        "inflight_comfort_index", "digital_exp_index", "service_quality_index", "ground_service_index",
        "ratings_sum", "ratings_mean", "ratings_std", "ratings_min", "ratings_max",
        "low_rating_count", "high_rating_count",
        "total_delay", "delay_recovery", "delay_per_distance", "is_delayed", "is_missing_arrival_delay",
        "class_travel_type", "customer_class"
    ]

    for feat in expected_features:
        assert feat in train_feat.columns, f"Feature {feat} missing from train"
        assert feat in test_feat.columns, f"Feature {feat} missing from test"
        assert feat in feature_names, f"Feature {feat} missing from feature_names list"

    # Verify no NaN values
    assert train_feat[feature_names].isnull().sum().sum() == 0
    assert test_feat[feature_names].isnull().sum().sum() == 0

def test_delay_imputation():
    train_df = create_sample_data(10)
    train_df.loc[0, "Arrival Delay in Minutes"] = np.nan
    train_df.loc[0, "Departure Delay in Minutes"] = 35.0

    train_feat, _, _ = generate_features(train_df, train_df.drop(columns=["satisfaction"]))

    assert train_feat.loc[0, "is_missing_arrival_delay"] == 1
    assert train_feat.loc[0, "total_delay"] == 70.0
    assert train_feat.loc[0, "delay_recovery"] == 0.0

def test_categorical_encoding():
    train_df = create_sample_data(20)
    test_df = create_sample_data(10).drop(columns=["satisfaction"])

    train_feat, test_feat, _ = generate_features(train_df, test_df)

    cat_cols = ["Gender", "Customer Type", "Type of Travel", "Class", "class_travel_type", "customer_class"]
    for c in cat_cols:
        assert np.issubdtype(train_feat[c].dtype, np.integer) or np.issubdtype(train_feat[c].dtype, np.floating)
        assert np.issubdtype(test_feat[c].dtype, np.integer) or np.issubdtype(test_feat[c].dtype, np.floating)
