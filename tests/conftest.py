"""
Pytest configuration and session fixtures for Kaggle S6E10 and JudgeGuard.
Ensures CI test environments have minimal valid dataset fixtures if raw Kaggle data is omitted from git.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.config import cfg

@pytest.fixture(scope="session", autouse=True)
def setup_ci_test_fixtures():
    """
    Session fixture that detects if raw Kaggle data files are missing (e.g. in headless CI),
    and deterministically synthesizes minimal valid CSV fixtures to enable complete pipeline testing.
    """
    if not cfg.TRAIN_PATH.exists():
        cfg.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        np.random.seed(42)
        n_samples = 300
        
        survey_cols = [
            'Inflight wifi service', 'Departure/Arrival time convenient', 'Ease of Online booking',
            'Gate location', 'Food and drink', 'Online boarding', 'Seat comfort',
            'Inflight entertainment', 'On-board service', 'Leg room service',
            'Baggage handling', 'Checkin service', 'Cleanliness'
        ]
        
        def _make_df(n, include_target=True):
            data = {
                'id': np.arange(n),
                'Age': np.random.randint(18, 75, size=n),
                'Flight Distance': np.random.randint(100, 3500, size=n),
                'Departure Delay in Minutes': np.random.choice([0, 5, 20, 60], size=n),
                'Arrival Delay in Minutes': np.random.choice([0.0, 10.0, np.nan, 45.0], size=n),
                'Gender': np.random.choice(['Male', 'Female'], size=n),
                'Customer Type': np.random.choice(['Loyal Customer', 'disloyal Customer'], size=n),
                'Type of Travel': np.random.choice(['Business travel', 'Personal Travel'], size=n),
                'Class': np.random.choice(['Eco', 'Business', 'Eco Plus'], size=n),
            }
            for col in survey_cols:
                data[col] = np.random.randint(1, 6, size=n)
                
            if include_target:
                data['satisfaction'] = np.random.choice([0, 1], size=n)
                
            return pd.DataFrame(data)

        train_df = _make_df(n_samples, include_target=True)
        test_df = _make_df(n_samples, include_target=False)
        sub_df = pd.DataFrame({'id': np.arange(n_samples), 'satisfaction': [0.5] * n_samples})

        train_df.to_csv(cfg.TRAIN_PATH, index=False)
        test_df.to_csv(cfg.TEST_PATH, index=False)
        sub_df.to_csv(cfg.SAMPLE_SUB_PATH, index=False)
