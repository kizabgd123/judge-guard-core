"""Configuration specification for Solar Filament Segmentation 2026.

Defines all constants, filepaths, GONG network station codes,
Panoptic Quality (PQ) hyperparameters, and CPU-only execution policies.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


# Base paths
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
DATA_DIR = PACKAGE_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DOCS_DIR = PACKAGE_ROOT / "docs"
KAGGLE_CPU_DIR = PACKAGE_ROOT / "kaggle_cpu"
NOTEBOOKS_DIR = PACKAGE_ROOT / "notebooks"
AGENTS_DIR = PACKAGE_ROOT / "agents"

# Competition metadata
COMPETITION_ID = "filament-segmentation-2026"
IMAGE_SHAPE: Tuple[int, int] = (2048, 2048)
EXPECTED_TEST_IMAGES_COUNT = 180
SUBMISSION_COLUMNS = ["filament_id", "segmentation_rle"]

# GONG Observatory Station Network Codes (found in file suffixes e.g. 20110120105534Ch.jpeg -> 'C')
GONG_STATIONS: Dict[str, str] = {
    "B": "Big Bear Solar Observatory (California, USA)",
    "C": "Cerro Tololo Inter-American Observatory (Chile)",
    "L": "Learmonth Solar Observatory (Australia)",
    "M": "Mauna Loa Solar Observatory (Hawaii, USA)",
    "T": "Observatorio del Teide (Tenerife, Spain)",
    "U": "Udaipur Solar Observatory (India)",
}

# Strict Kaggle Compute Constraints
ENABLE_GPU: bool = False  # Strictly False per user mandate
CPU_THREADS: int = 4
BATCH_SIZE_CPU: int = 1

# Panoptic Quality (PQ) & Morphological Hyperparameters
@dataclass(frozen=True)
class PipelineParams:
    # Morphological and instance partitioning
    iou_match_threshold: float = 0.5
    min_instance_area: int = 250
    morph_close_kernel_size: int = 5
    voronoi_min_distance: int = 15
    hann_tile_size: int = 512
    hann_tile_overlap: int = 64
    
    # Probability gating
    prob_threshold: float = 0.45
    seed_prob_threshold: float = 0.70
    
    # Expected bounds for sanity validation
    min_acceptable_instances: int = 1200
    max_acceptable_instances: int = 1450


PARAMS = PipelineParams()
