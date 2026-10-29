"""Topology-Safe Voronoi Post-Processing & COCO RLE Codec.

Critical for optimizing Panoptic Quality (PQ):
- Prevents catastrophic filament fragmentation.
- Separates touching filaments without snapping thin spines.
- Generates official competition COCO RLE representations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.ndimage import distance_transform_edt, maximum_filter

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from pycocotools import mask as mask_utils
except ImportError:
    mask_utils = None


logger = logging.getLogger("filament.postprocess")


# ---------------------------------------------------------------------------
# Compressed COCO RLE Codec
# ---------------------------------------------------------------------------

def mask_to_rle(binary_mask: np.ndarray) -> str:
    """Encode 2D binary mask to compressed COCO RLE string."""
    if mask_utils is not None:
        fortran_mask = np.asfortranarray(binary_mask.astype(np.uint8))
        encoded = mask_utils.encode(fortran_mask)
        if isinstance(encoded["counts"], bytes):
            return encoded["counts"].decode("utf-8")
        return encoded["counts"]
    
    # Pure python/numpy fallback if pycocotools is missing
    pixels = binary_mask.flatten(order="F")
    runs = []
    prev = 0
    count = 0
    for p in pixels:
        val = 1 if p else 0
        if val == prev:
            count += 1
        else:
            runs.append(count)
            count = 1
            prev = val
    runs.append(count)
    return " ".join(map(str, runs))


def rle_to_mask(rle_string: str, height: int = 2048, width: int = 2048) -> np.ndarray:
    """Decode compressed COCO RLE string to 2D boolean mask."""
    if mask_utils is not None and not (" " in rle_string and rle_string.replace(" ", "").isdigit()):
        rle_dict = {
            "size": [height, width],
            "counts": rle_string.encode("utf-8") if isinstance(rle_string, str) else rle_string,
        }
        decoded = mask_utils.decode(rle_dict)
        return decoded.astype(bool)

    # Pure python run-length decode fallback
    if " " in rle_string:
        counts = [int(x) for x in rle_string.split()]
        pixels = np.zeros(height * width, dtype=bool)
        idx = 0
        val = False
        for c in counts:
            if val:
                pixels[idx:idx + c] = True
            idx += c
            val = not val
        return pixels.reshape((height, width), order="F")

    raise ValueError("Cannot decode RLE without pycocotools or whitespace-delimited counts")


# ---------------------------------------------------------------------------
# Morphological & Topological Refinement
# ---------------------------------------------------------------------------

def morphological_close_hairline(binary_mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Bridge 1-2px hairline spine fractures without bridging separate filaments."""
    if cv2 is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        closed = cv2.morphologyEx(binary_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
        return closed > 0
    
    from scipy.ndimage import binary_closing
    struct = np.ones((kernel_size, kernel_size), dtype=bool)
    return binary_closing(binary_mask, structure=struct)


def count_connected_components(binary_mask: np.ndarray) -> Tuple[int, np.ndarray]:
    """Return component count and labeled map using 8-connectivity."""
    if cv2 is not None:
        num_labels, labels = cv2.connectedComponents(binary_mask.astype(np.uint8), connectivity=8)
        return num_labels - 1, labels
    
    from scipy.ndimage import label
    struct = np.ones((3, 3), dtype=bool)
    labels, num = label(binary_mask, structure=struct)
    return num, labels


def voronoi_partition_instances(
    prob_map: np.ndarray,
    prob_threshold: float = 0.45,
    seed_threshold: float = 0.70,
    min_distance: int = 15,
    min_area: int = 250,
    morph_kernel: int = 5,
) -> List[np.ndarray]:
    """Decompose continuous probability map into discrete filament instances.
    
    Uses distance-transform ridge detection to seed Voronoi cells, preventing
    catastrophic over-merging while pruning sub-threshold fibril noise.
    Prevents spine fragmentation by analyzing constriction necks per component.
    """
    binary = prob_map >= prob_threshold
    if not np.any(binary):
        return []

    # Step 1: Bridge micro-fractures along spine
    closed = morphological_close_hairline(binary, kernel_size=morph_kernel)

    # Step 2: Extract initial connected components
    num_comp, labels = count_connected_components(closed)
    if num_comp == 0:
        return []

    instances: List[np.ndarray] = []
    min_seed_sz = max(3, min_area // 20)

    for c in range(1, num_comp + 1):
        comp = (labels == c)
        comp_area = int(np.sum(comp))
        if comp_area < min_area:
            continue

        # Check if component contains multiple touching filaments separated by a bottleneck
        dist = distance_transform_edt(comp)
        max_d = float(dist.max())
        split_found = False

        if max_d >= 3.0 and cv2 is not None:
            # Check progressive seed thresholds along distance ridge
            for thresh_ratio in [0.45, 0.55, 0.65]:
                d_thresh = max_d * thresh_ratio
                seeds_mask = comp & (prob_map >= seed_threshold) & (dist >= d_thresh)
                n_seeds, s_labels = count_connected_components(seeds_mask)

                valid_seed_indices = [
                    s for s in range(1, n_seeds + 1) if np.sum(s_labels == s) >= min_seed_sz
                ]

                if len(valid_seed_indices) >= 2:
                    # Multi-core junction detected: perform Voronoi watershed partition
                    markers = np.zeros(comp.shape, dtype=np.int32)
                    for idx_s, s_val in enumerate(valid_seed_indices, start=1):
                        markers[s_labels == s_val] = idx_s

                    dist_uint8 = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    dist_3ch = cv2.cvtColor(255 - dist_uint8, cv2.COLOR_GRAY2BGR)
                    cv2.watershed(dist_3ch, markers)

                    for idx_s in range(1, len(valid_seed_indices) + 1):
                        sub_inst = (markers == idx_s) & comp
                        if np.sum(sub_inst) >= min_area:
                            instances.append(sub_inst)
                    split_found = True
                    break

        if not split_found:
            instances.append(comp)

    return instances
