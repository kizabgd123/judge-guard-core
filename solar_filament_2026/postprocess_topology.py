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
    """
    binary = prob_map >= prob_threshold
    if not np.any(binary):
        return []

    # Step 1: Bridge micro-fractures along spine
    closed = morphological_close_hairline(binary, kernel_size=morph_kernel)

    # Step 2: Distance transform inside high-confidence regions
    dist = distance_transform_edt(closed)

    # Step 3: Find local maxima (seeds for instances)
    # Only keep peaks above seed threshold probability
    valid_seed_region = (prob_map >= seed_threshold) & (dist > 2.0)
    
    if not np.any(valid_seed_region):
        # Fallback to connected components if no high-confidence peaks
        num_comp, labels = count_connected_components(closed)
        instances = []
        for c in range(1, num_comp + 1):
            mask = (labels == c)
            if np.sum(mask) >= min_area:
                instances.append(mask)
        return instances

    # Local maximum filter for peak finding
    size = 2 * min_distance + 1
    local_max = maximum_filter(dist, size=size) == dist
    peaks = local_max & valid_seed_region & closed

    # Label seeds
    seed_count, seed_labels = count_connected_components(peaks)
    if seed_count <= 1:
        # Single instance or flat region
        num_comp, labels = count_connected_components(closed)
        instances = []
        for c in range(1, num_comp + 1):
            mask = (labels == c)
            if np.sum(mask) >= min_area:
                instances.append(mask)
        return instances

    # Step 4: Propagate seeds to fill foreground mask via Voronoi distance
    # For each foreground pixel, find closest seed
    if cv2 is not None:
        # Fast watershed propagation
        markers = seed_labels.astype(np.int32)
        # Background = 0, unknown/foreground = 0, markers > 0
        img_3ch = cv2.cvtColor((prob_map * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        markers[~closed] = 0
        markers[closed & (seed_labels == 0)] = 0
        
        # Invert distance for watershed
        dist_uint8 = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        dist_3ch = cv2.cvtColor(255 - dist_uint8, cv2.COLOR_GRAY2BGR)
        
        cv2.watershed(dist_3ch, markers)
        unique_labels = np.unique(markers)
        
        instances = []
        for lbl in unique_labels:
            if lbl > 0:
                mask = (markers == lbl) & closed
                if np.sum(mask) >= min_area:
                    instances.append(mask)
        return instances

    # Fallback to connected components
    num_comp, labels = count_connected_components(closed)
    instances = []
    for c in range(1, num_comp + 1):
        mask = (labels == c)
        if np.sum(mask) >= min_area:
            instances.append(mask)
    return instances
