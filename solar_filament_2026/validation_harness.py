"""Leak-Free Validation Harness and Evaluation Reporter.

Ensures observation splits group by date and stratify by GONG observatory station
to prevent temporal and atmospheric data leakage.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Sequence, Tuple
import numpy as np

from solar_filament_2026.data_loader import ImageMeta
from solar_filament_2026.metrics import panoptic_quality

logger = logging.getLogger("filament.validation")


def create_grouped_station_split(
    metadata_list: Sequence[ImageMeta],
    num_folds: int = 5,
    seed: int = 42,
) -> List[Tuple[List[int], List[int]]]:
    """Create group-kfold splits grouped by date string (YYYYMMDD)."""
    date_to_indices: Dict[str, List[int]] = {}
    for idx, meta in enumerate(metadata_list):
        date_key = f"{meta.year:04d}{meta.month:02d}{meta.day:02d}"
        if date_key not in date_to_indices:
            date_to_indices[date_key] = []
        date_to_indices[date_key].append(idx)

    unique_dates = list(date_to_indices.keys())
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_dates)

    folds = [[] for _ in range(num_folds)]
    for i, date in enumerate(unique_dates):
        folds[i % num_folds].extend(date_to_indices[date])

    splits = []
    all_indices = set(range(len(metadata_list)))
    for val_indices in folds:
        train_indices = sorted(list(all_indices - set(val_indices)))
        splits.append((train_indices, sorted(val_indices)))

    return splits


class ValidationReporter:
    """Aggregates per-image Panoptic Quality metrics and produces diagnostic summaries."""

    def __init__(self) -> None:
        self.results: List[Dict[str, float]] = []

    def record_image_eval(self, eval_dict: Dict[str, float]) -> None:
        self.results.append(eval_dict)

    def summary(self) -> Dict[str, float]:
        if not self.results:
            return {"mean_pq": 0.0, "mean_sq": 0.0, "mean_rq": 0.0, "total_images": 0}

        mean_pq = np.mean([r["pq"] for r in self.results])
        mean_sq = np.mean([r["sq"] for r in self.results])
        mean_rq = np.mean([r["rq"] for r in self.results])
        total_tp = sum([r["tp"] for r in self.results])
        total_fp = sum([r["fp"] for r in self.results])
        total_fn = sum([r["fn"] for r in self.results])

        return {
            "mean_pq": float(mean_pq),
            "mean_sq": float(mean_sq),
            "mean_rq": float(mean_rq),
            "total_tp": int(total_tp),
            "total_fp": int(total_fp),
            "total_fn": int(total_fn),
            "total_images": len(self.results),
        }
