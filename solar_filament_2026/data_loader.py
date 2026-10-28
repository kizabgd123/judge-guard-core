"""GONG Solar H-alpha Observation Data Loader.

Handles 2048x2048 solar disk images, parses GONG observatory station codes,
extracts solar limb coordinates, and provides normalization.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from solar_filament_2026.config import GONG_STATIONS, IMAGE_SHAPE


@dataclass
class ImageMeta:
    """Metadata extracted from GONG observation filename."""
    filename: str
    filepath: Path
    timestamp_str: str
    station_code: str
    station_name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int


def parse_filename(filepath: str | Path) -> ImageMeta:
    """Parse GONG filename format: YYYYMMDDHHMMSSSh.jpeg (e.g. 20110120105534Ch.jpeg)."""
    p = Path(filepath)
    name = p.stem  # e.g. 20110120105534Ch
    
    match = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})([BCLMTU])h?", name)
    if not match:
        # Fallback if pattern does not strictly match
        station = "C"
        for c in GONG_STATIONS.keys():
            if c in name:
                station = c
                break
        return ImageMeta(
            filename=p.name,
            filepath=p,
            timestamp_str="unknown",
            station_code=station,
            station_name=GONG_STATIONS.get(station, "Unknown Station"),
            year=2026, month=1, day=1, hour=0, minute=0, second=0
        )
    
    year, month, day, hour, minute, second, station = match.groups()
    return ImageMeta(
        filename=p.name,
        filepath=p,
        timestamp_str=f"{year}-{month}-{day}T{hour}:{minute}:{second}Z",
        station_code=station,
        station_name=GONG_STATIONS.get(station, "Unknown Station"),
        year=int(year),
        month=int(month),
        day=int(day),
        hour=int(hour),
        minute=int(minute),
        second=int(second),
    )


def load_solar_image(filepath: str | Path, target_shape: Tuple[int, int] = IMAGE_SHAPE) -> np.ndarray:
    """Load solar observation image as single-channel normalized float32 array in [0, 1]."""
    path_str = str(filepath)
    if not os.path.exists(path_str):
        raise FileNotFoundError(f"Image not found at {path_str}")

    if cv2 is not None:
        img = cv2.imread(path_str, cv2.IMREAD_GRAYSCALE)
    else:
        from PIL import Image
        pil_img = Image.open(path_str).convert("L")
        img = np.array(pil_img)

    if img is None:
        raise ValueError(f"Failed to read image at {path_str}")

    if img.shape != target_shape:
        if cv2 is not None:
            img = cv2.resize(img, (target_shape[1], target_shape[0]), interpolation=cv2.INTER_AREA)
        else:
            from PIL import Image
            pil_img = Image.fromarray(img).resize((target_shape[1], target_shape[0]), Image.Resampling.BILINEAR)
            img = np.array(pil_img)

    return img.astype(np.float32) / 255.0


def create_synthetic_solar_disk(
    shape: Tuple[int, int] = (512, 512),
    radius_ratio: float = 0.42,
    num_filaments: int = 3,
    seed: int = 42,
) -> Tuple[np.ndarray, List[np.ndarray]]:
    """Generate a clean synthetic solar disk with ground-truth filaments for unit tests."""
    rng = np.random.RandomState(seed)
    h, w = shape
    cy, cx = h // 2, w // 2
    r = int(min(h, w) * radius_ratio)

    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    disk_mask = dist_from_center <= r

    # Solar disk with limb darkening
    limb = np.zeros((h, w), dtype=np.float32)
    norm_dist = np.clip(dist_from_center / max(1, r), 0.0, 1.0)
    limb[disk_mask] = np.sqrt(np.clip(1.0 - norm_dist[disk_mask] ** 2, 0.0, 1.0)) * 0.7 + 0.3

    filament_masks = []
    # Add filament absorption features (dark curves)
    for i in range(num_filaments):
        f_mask = np.zeros((h, w), dtype=bool)
        # random center inside disk
        angle = rng.uniform(0, 2 * np.pi)
        dist = rng.uniform(0.1, 0.7) * r
        fy = int(cy + dist * np.sin(angle))
        fx = int(cx + dist * np.cos(angle))
        
        # draw curve
        length = rng.randint(40, 80)
        theta = rng.uniform(0, np.pi)
        thickness = rng.randint(2, 6)
        
        for step in range(-length // 2, length // 2):
            py = int(fy + step * np.sin(theta) + rng.uniform(-1, 1))
            px = int(fx + step * np.cos(theta) + rng.uniform(-1, 1))
            if 0 <= py < h and 0 <= px < w and disk_mask[py, px]:
                f_mask[max(0, py - thickness // 2):min(h, py + thickness // 2 + 1),
                       max(0, px - thickness // 2):min(w, px + thickness // 2 + 1)] = True

        if np.sum(f_mask) > 50:
            limb[f_mask] *= 0.35  # dark absorption
            filament_masks.append(f_mask)

    return limb, filament_masks
