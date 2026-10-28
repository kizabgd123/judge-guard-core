"""
Automated Kaggle CLI Submission and Validator for Playground Series S6E10.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np

COMPETITION_NAME = "playground-series-s6e10"
DEFAULT_SAMPLE_PATH = Path("data/raw/sample_submission.csv")

def validate_submission(
    sub_path: Path,
    sample_path: Path = DEFAULT_SAMPLE_PATH,
    expected_rows: int = 299844
) -> bool:
    """
    Validates submission schema, dimensions, and numerical validity against sample_submission.
    """
    sub_path = Path(sub_path)
    sample_path = Path(sample_path)

    if not sub_path.exists():
        raise FileNotFoundError(f"Submission file does not exist: {sub_path}")

    sub_df = pd.read_csv(sub_path)

    # Check columns
    expected_cols = ["id", "satisfaction"]
    if list(sub_df.columns) != expected_cols:
        raise ValueError(f"Columns mismatch: expected {expected_cols}, got {list(sub_df.columns)}")

    # Check row count
    if expected_rows is not None and len(sub_df) != expected_rows:
        raise ValueError(f"Row count mismatch: expected {expected_rows}, got {len(sub_df)}")

    # Check NaNs
    if sub_df["satisfaction"].isnull().any():
        raise ValueError("Submission contains NaN or Null values in 'satisfaction' column!")

    # Check probability bounds
    if (sub_df["satisfaction"] < 0.0).any() or (sub_df["satisfaction"] > 1.0).any():
        raise ValueError("Predictions contain values outside [0.0, 1.0] interval!")

    # Check ID alignment if sample_submission exists
    if sample_path.exists():
        sample_df = pd.read_csv(sample_path)
        if len(sub_df) == len(sample_df):
            if not np.array_equal(sub_df["id"].values, sample_df["id"].values):
                raise ValueError("Submission 'id' values do not match sample_submission.csv!")

    return True

def submit_to_kaggle(
    sub_path: Path,
    message: str,
    competition: str = COMPETITION_NAME
) -> str:
    """
    Executes kaggle CLI submission and checks status.
    """
    sub_path = Path(sub_path)
    validate_submission(sub_path)

    cmd = [
        sys.executable.replace("python", "kaggle"),
        "competitions", "submit",
        "-c", competition,
        "-f", str(sub_path),
        "-m", message
    ]
    # Fallback to kaggle if direct venv path differs
    if not Path(cmd[0]).exists():
        cmd[0] = "kaggle"

    print(f"🚀 Submitting {sub_path.name} to {competition}...")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(result.stdout)

    # Check status
    status_cmd = [cmd[0], "competitions", "submissions", "-c", competition]
    status_res = subprocess.run(status_cmd, capture_output=True, text=True, check=True)
    print("📋 Recent Submissions:")
    print(status_res.stdout[:1000])

    return result.stdout

def main():
    parser = argparse.ArgumentParser(description="Validate and submit predictions to Kaggle")
    parser.add_argument("file", type=str, help="Path to submission CSV")
    parser.add_argument("-m", "--message", type=str, default="Automated competitive ML submission", help="Submission note")
    parser.add_argument("--validate-only", action="store_true", help="Only validate without submitting")
    args = parser.parse_args()

    sub_file = Path(args.file)
    print(f"Checking {sub_file}...")
    validate_submission(sub_file)
    print("✅ Submission file passed all schema and value checks.")

    if not args.validate_only:
        submit_to_kaggle(sub_file, args.message)

if __name__ == "__main__":
    main()
