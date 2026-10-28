"""
Feature engineering and preprocessing pipeline for Kaggle S6E10.
Implements domain-specific delay transformations, survey aggregations,
pain point indicators, and interaction features.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List
from sklearn.preprocessing import OrdinalEncoder
from src.config import cfg

class FeatureEngineer:
    def __init__(self):
        self.encoder = None
        self.feature_names = []

    def fit_transform(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        train = train_df.copy()
        test = test_df.copy()

        # 1. Impute missing Arrival Delay using Departure Delay
        train['Arrival Delay in Minutes'] = train['Arrival Delay in Minutes'].fillna(train['Departure Delay in Minutes'])
        test['Arrival Delay in Minutes'] = test['Arrival Delay in Minutes'].fillna(test['Departure Delay in Minutes'])

        # 2. Delay Features
        for df in [train, test]:
            df['Total_Delay'] = df['Departure Delay in Minutes'] + df['Arrival Delay in Minutes']
            df['Delay_Diff'] = df['Arrival Delay in Minutes'] - df['Departure Delay in Minutes']
            df['Is_Delayed'] = ((df['Departure Delay in Minutes'] > 0) | (df['Arrival Delay in Minutes'] > 0)).astype(np.int8)
            df['Severe_Delay'] = ((df['Departure Delay in Minutes'] > 60) | (df['Arrival Delay in Minutes'] > 60)).astype(np.int8)
            df['Delay_Ratio'] = df['Total_Delay'] / (df['Flight Distance'] + 1.0)
            df['Flight_Made_Up_Time'] = (df['Delay_Diff'] < 0).astype(np.int8)

        # 3. Survey Aggregations (across all 13 survey dimensions)
        survey_cols = [c for c in cfg.SURVEY_COLS if c in train.columns]
        for df in [train, test]:
            df['Survey_Mean'] = df[survey_cols].mean(axis=1)
            df['Survey_Std'] = df[survey_cols].std(axis=1)
            df['Survey_Sum'] = df[survey_cols].sum(axis=1)
            df['Survey_Min'] = df[survey_cols].min(axis=1)
            df['Survey_Max'] = df[survey_cols].max(axis=1)
            # Pain points (low rating <= 2) and Delights (>= 4)
            df['Survey_Pain_Points'] = (df[survey_cols] <= 2).sum(axis=1)
            df['Survey_Delight_Points'] = (df[survey_cols] >= 4).sum(axis=1)

            # Group scores
            df['Comfort_Score'] = df[['Seat comfort', 'Leg room service', 'Cleanliness']].mean(axis=1)
            df['Digital_Score'] = df[['Inflight wifi service', 'Ease of Online booking', 'Online boarding']].mean(axis=1)
            df['Service_Score'] = df[['On-board service', 'Baggage handling', 'Checkin service']].mean(axis=1)
            df['Convenience_Score'] = df[['Gate location', 'Departure/Arrival time convenient']].mean(axis=1)

            # Ratio / Interaction Features
            df['Distance_Per_Age'] = df['Flight Distance'] / (df['Age'] + 1.0)
            df['Online_vs_Wifi'] = df['Online boarding'] - df['Inflight wifi service']

            # High value cross-categoricals
            df['Class_TravelType'] = df['Class'].astype(str) + "_" + df['Type of Travel'].astype(str)
            df['Customer_Class'] = df['Customer Type'].astype(str) + "_" + df['Class'].astype(str)

        new_cat_cols = cfg.CATEGORICAL_COLS + ['Class_TravelType', 'Customer_Class']

        # 4. Ordinal encoding for tree-based models
        self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        train[new_cat_cols] = self.encoder.fit_transform(train[new_cat_cols].astype(str))
        test[new_cat_cols] = self.encoder.transform(test[new_cat_cols].astype(str))

        ignore_cols = [cfg.ID_COL, cfg.TARGET_COL]
        self.feature_names = [c for c in train.columns if c not in ignore_cols]

        return train, test
