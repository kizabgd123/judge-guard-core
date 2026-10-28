"""
Configuration settings for Kaggle Playground Series s6e10.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent

@dataclass
class Config:
    # Competition Metadata
    COMPETITION_NAME: str = "playground-series-s6e10"
    TARGET_COL: str = "satisfaction"
    ID_COL: str = "id"
    EVAL_METRIC: str = "roc_auc"
    RANDOM_SEED: int = 42
    N_FOLDS: int = 5

    # Paths
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    SUBMISSIONS_DIR: Path = PROJECT_ROOT / "submissions"

    TRAIN_PATH: Path = RAW_DATA_DIR / "train.csv"
    TEST_PATH: Path = RAW_DATA_DIR / "test.csv"
    SAMPLE_SUB_PATH: Path = RAW_DATA_DIR / "sample_submission.csv"

    # Columns definitions
    CATEGORICAL_COLS: List[str] = field(default_factory=lambda: [
        "Gender",
        "Customer Type",
        "Type of Travel",
        "Class"
    ])

    NUMERIC_COLS: List[str] = field(default_factory=lambda: [
        "Age",
        "Flight Distance",
        "Departure Delay in Minutes",
        "Arrival Delay in Minutes"
    ])

    SURVEY_COLS: List[str] = field(default_factory=lambda: [
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
        "Baggage handling",
        "Checkin service",
        "Cleanliness"
    ])

cfg = Config()
