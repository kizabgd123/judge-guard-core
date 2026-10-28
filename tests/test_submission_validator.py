"""
Unit tests for submission validator (scripts/submit.py).
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from scripts.submit import validate_submission

def test_validate_submission_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sample_path = tmp_path / "sample.csv"
        sub_path = tmp_path / "sub.csv"

        df_sample = pd.DataFrame({"id": [1, 2, 3], "satisfaction": [0.5, 0.5, 0.5]})
        df_sub = pd.DataFrame({"id": [1, 2, 3], "satisfaction": [0.1, 0.85, 0.42]})

        df_sample.to_csv(sample_path, index=False)
        df_sub.to_csv(sub_path, index=False)

        assert validate_submission(sub_path, sample_path, expected_rows=3) is True

def test_validate_submission_invalid_columns():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sample_path = tmp_path / "sample.csv"
        sub_path = tmp_path / "sub.csv"

        df_sample = pd.DataFrame({"id": [1, 2], "satisfaction": [0.5, 0.5]})
        df_sub = pd.DataFrame({"id": [1, 2], "target": [0.1, 0.85]})

        df_sample.to_csv(sample_path, index=False)
        df_sub.to_csv(sub_path, index=False)

        with pytest.raises(ValueError, match="Columns mismatch"):
            validate_submission(sub_path, sample_path, expected_rows=2)

def test_validate_submission_nan_or_bounds():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sample_path = tmp_path / "sample.csv"
        sub_path = tmp_path / "sub.csv"

        df_sample = pd.DataFrame({"id": [1, 2], "satisfaction": [0.5, 0.5]})
        df_sub_nan = pd.DataFrame({"id": [1, 2], "satisfaction": [0.1, np.nan]})

        df_sample.to_csv(sample_path, index=False)
        df_sub_nan.to_csv(sub_path, index=False)

        with pytest.raises(ValueError, match="NaN or Null"):
            validate_submission(sub_path, sample_path, expected_rows=2)
