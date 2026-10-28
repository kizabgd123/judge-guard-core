"""
Feature Engineering Engine for Kaggle Playground Series S6E10.
Computes domain indices, per-row survey stats, delay metrics, and categorical crosses.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List
from sklearn.preprocessing import OrdinalEncoder

SURVEY_FEATURES: List[str] = [
    "Inflight wifi service",
    "Departure/Arrival time convenient",
    "Ease of Online booking",
    "Gate location",
    "Food and drink",
    "Online boarding",
    "Seat comfort",
    "Inflight entertainment",
    "On-board service",
    "Leg room service",
    "Checkin service",
    "Cleanliness"
]

def generate_features(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Transforms train and test datasets with domain-specific features.
    Returns:
        (transformed_train, transformed_test, list_of_feature_names)
    """
    train = train_df.copy()
    test = test_df.copy()

    for df in [train, test]:
        # 1. Missing arrival delay handling & flight dynamics
        df["is_missing_arrival_delay"] = df["Arrival Delay in Minutes"].isnull().astype(np.int8)
        df["Arrival Delay in Minutes"] = df["Arrival Delay in Minutes"].fillna(df["Departure Delay in Minutes"])

        df["total_delay"] = df["Departure Delay in Minutes"] + df["Arrival Delay in Minutes"]
        df["delay_recovery"] = df["Arrival Delay in Minutes"] - df["Departure Delay in Minutes"]
        df["delay_per_distance"] = df["total_delay"] / (df["Flight Distance"] + 1.0)
        df["is_delayed"] = (df["total_delay"] > 0).astype(np.int8)

        # 2. Domain satisfaction indices
        df["inflight_comfort_index"] = df[["Seat comfort", "Inflight entertainment", "Cleanliness", "Food and drink"]].mean(axis=1)
        df["digital_exp_index"] = df[["Inflight wifi service", "Ease of Online booking"]].mean(axis=1)
        df["service_quality_index"] = df[["On-board service", "Leg room service", "Checkin service"]].mean(axis=1)
        df["ground_service_index"] = df[["Checkin service", "Gate location", "Departure/Arrival time convenient"]].mean(axis=1)

        # 3. Per-row rating statistics
        survey_slice = df[SURVEY_FEATURES]
        df["ratings_sum"] = survey_slice.sum(axis=1)
        df["ratings_mean"] = survey_slice.mean(axis=1)
        df["ratings_std"] = survey_slice.std(axis=1).fillna(0.0)
        df["ratings_min"] = survey_slice.min(axis=1)
        df["ratings_max"] = survey_slice.max(axis=1)
        df["low_rating_count"] = (survey_slice <= 2).sum(axis=1)
        df["high_rating_count"] = (survey_slice >= 4).sum(axis=1)

        # 4. Categorical crosses
        df["class_travel_type"] = df["Class"].astype(str) + "_" + df["Type of Travel"].astype(str)
        df["customer_class"] = df["Customer Type"].astype(str) + "_" + df["Class"].astype(str)

    # 5. Encoding categoricals
    cat_cols = ["Gender", "Customer Type", "Type of Travel", "Class", "class_travel_type", "customer_class"]
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    train[cat_cols] = encoder.fit_transform(train[cat_cols].astype(str))
    test[cat_cols] = encoder.transform(test[cat_cols].astype(str))

    ignore_cols = ["id", "satisfaction"]
    feature_names = [col for col in train.columns if col not in ignore_cols]

    return train, test, feature_names
