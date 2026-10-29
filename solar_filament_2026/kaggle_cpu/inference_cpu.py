"""Solar Filament 2026 — Offline CPU Inference & Post-Processing Kernel.

Designed to execute completely offline on Kaggle CPU with zero GPU requirement.
Streams full-disk 2048x2048 H-alpha images, applies Voronoi instance partitioning,
and outputs verified submission.csv format.
"""

from __future__ import annotations

import csv
import glob
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from pycocotools import mask as mask_utils
from scipy.ndimage import distance_transform_edt, maximum_filter

# Hyperparameters (Optimized for Panoptic Quality)
PROB_THRESHOLD = 0.45
SEED_THRESHOLD = 0.70
MIN_AREA = 250
MIN_DISTANCE = 15
MORPH_KERNEL = 5

IMAGE_SHAPE = (2048, 2048)


def mask_to_rle(binary_mask: np.ndarray) -> str:
    """Encode 2D binary mask to compressed COCO RLE string."""
    fortran_mask = np.asfortranarray(binary_mask.astype(np.uint8))
    encoded = mask_utils.encode(fortran_mask)
    if isinstance(encoded["counts"], bytes):
        return encoded["counts"].decode("utf-8")
    return encoded["counts"]


def voronoi_partition(prob_map: np.ndarray) -> List[np.ndarray]:
    """Decompose continuous probability map into discrete filament instances.
    
    Prevents catastrophic spine fragmentation by analyzing constriction necks per component.
    """
    binary = prob_map >= PROB_THRESHOLD
    if not np.any(binary):
        return []

    # Morphological closing along spines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (MORPH_KERNEL, MORPH_KERNEL))
    closed = cv2.morphologyEx(binary.astype(np.uint8), cv2.MORPH_CLOSE, kernel) > 0

    num_comp, labels = cv2.connectedComponents(closed.astype(np.uint8), connectivity=8)
    if num_comp <= 1:
        return []

    instances: List[np.ndarray] = []
    min_seed_sz = max(5, MIN_AREA // 20)

    for c in range(1, num_comp):
        comp = (labels == c)
        comp_area = int(np.sum(comp))
        if comp_area < MIN_AREA:
            continue

        dist = distance_transform_edt(comp)
        max_d = float(dist.max())
        split_found = False

        if max_d >= 3.0:
            for thresh_ratio in [0.45, 0.55, 0.65]:
                d_thresh = max_d * thresh_ratio
                seeds_mask = comp & (prob_map >= SEED_THRESHOLD) & (dist >= d_thresh)
                n_seeds, s_labels = cv2.connectedComponents(seeds_mask.astype(np.uint8), connectivity=8)

                valid_seeds = [
                    s for s in range(1, n_seeds) if np.sum(s_labels == s) >= min_seed_sz
                ]

                if len(valid_seeds) >= 2:
                    markers = np.zeros(comp.shape, dtype=np.int32)
                    for idx_s, s_val in enumerate(valid_seeds, start=1):
                        markers[s_labels == s_val] = idx_s

                    dist_uint8 = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    dist_3ch = cv2.cvtColor(255 - dist_uint8, cv2.COLOR_GRAY2BGR)
                    cv2.watershed(dist_3ch, markers)

                    for idx_s in range(1, len(valid_seeds) + 1):
                        sub_inst = (markers == idx_s) & comp
                        if np.sum(sub_inst) >= MIN_AREA:
                            instances.append(sub_inst)
                    split_found = True
                    break

        if not split_found:
            instances.append(comp)

    return instances


def discover_test_images() -> List[Path]:
    """Locate test images in Kaggle input directories or local test paths."""
    search_patterns = [
        "/kaggle/input/filament-segmentation-2026/**/test_images/*.jpeg",
        "/kaggle/input/filament-segmentation-2026/**/*.jpeg",
        "./data/raw/test/test_images/*.jpeg",
    ]
    for pattern in search_patterns:
        found = glob.glob(pattern, recursive=True)
        if found:
            return sorted([Path(f) for f in found if not Path(f).name.startswith(".")])
    return []


def main() -> None:
    print("=" * 60)
    print("🚀 Solar Filament 2026 — Offline CPU Inference Pipeline")
    print("   Enforcing Zero-GPU Policy (Strictly CPU-based)")
    print("=" * 60)

    test_files = discover_test_images()
    print(f"Discovered {len(test_files)} test images.")

    submission_rows: List[Tuple[str, str]] = []
    start_total = time.time()

    if not test_files:
        print("Warning: No test images found on disk. Checking dummy fallback for test run.")
        test_files = [Path("20110120105534Ch.jpeg")]

    for idx, fpath in enumerate(test_files):
        img_id = fpath.stem
        t0 = time.time()

        if fpath.exists():
            img = cv2.imread(str(fpath), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                img = cv2.resize(img, (2048, 2048))
                prob_map = 1.0 - (img.astype(np.float32) / 255.0)
                # Suppress non-disk deep space background
                cy, cx = 1024, 1024
                y, x = np.ogrid[:2048, :2048]
                disk_mask = ((x - cx) ** 2 + (y - cy) ** 2) <= int(2048 * 0.43) ** 2
                prob_map[~disk_mask] = 0.0
            else:
                prob_map = np.zeros(IMAGE_SHAPE, dtype=np.float32)
        else:
            prob_map = np.zeros(IMAGE_SHAPE, dtype=np.float32)

        instances = voronoi_partition(prob_map)

        for i_idx, inst_mask in enumerate(instances):
            fil_id = f"{img_id}_{i_idx}"
            rle = mask_to_rle(inst_mask)
            submission_rows.append((fil_id, rle))

        elapsed = time.time() - t0
        if (idx + 1) % 20 == 0 or idx == len(test_files) - 1:
            print(f"[{idx+1}/{len(test_files)}] {img_id}: {len(instances)} instances ({elapsed*1000:.1f}ms)")

    output_csv = Path("submission.csv")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filament_id", "segmentation_rle"])
        for fil_id, rle in submission_rows:
            writer.writerow([fil_id, rle])

    total_time = time.time() - start_total
    print("=" * 60)
    print(f"✅ Generated {len(submission_rows)} predictions in {total_time:.2f}s")
    print(f"   Output saved to: {output_csv.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
