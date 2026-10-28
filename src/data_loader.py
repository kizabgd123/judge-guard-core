"""
Data loading and memory optimization utility for Playground Series s6e10.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from src.config import cfg

def reduce_mem_usage(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """Downcast numeric types to reduce RAM usage."""
    start_mem = df.memory_usage().sum() / 1024**2
    for col in df.columns:
        col_type = df[col].dtype
        if col_type != object and not isinstance(col_type, pd.CategoricalDtype):
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            elif str(col_type)[:5] == 'float':
                df[col] = df[col].astype(np.float32)
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print(f"Memory decreased from {start_mem:.2f}MB to {end_mem:.2f}MB ({(1 - end_mem/start_mem)*100:.1f}% reduction)")
    return df

def load_data(
    train_path: Optional[Path] = None,
    test_path: Optional[Path] = None,
    sample_sub_path: Optional[Path] = None,
    nrows: Optional[int] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads train, test, and sample submission files."""
    train_path = train_path or cfg.TRAIN_PATH
    test_path = test_path or cfg.TEST_PATH
    sample_sub_path = sample_sub_path or cfg.SAMPLE_SUB_PATH

    train = pd.read_csv(train_path, nrows=nrows)
    test = pd.read_csv(test_path, nrows=nrows)
    sub = pd.read_csv(sample_sub_path, nrows=nrows)

    # Standardize target to int (0 / 1)
    if cfg.TARGET_COL in train.columns:
        if train[cfg.TARGET_COL].dtype == bool:
            train[cfg.TARGET_COL] = train[cfg.TARGET_COL].astype(int)
        elif train[cfg.TARGET_COL].dtype == object:
            train[cfg.TARGET_COL] = train[cfg.TARGET_COL].apply(
                lambda x: 1 if str(x).lower() in ['1', 'true', 'satisfied'] else 0
            )

    train = reduce_mem_usage(train)
    test = reduce_mem_usage(test)

    return train, test, sub
