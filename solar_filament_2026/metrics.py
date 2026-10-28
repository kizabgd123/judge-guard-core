"""Panoptic Quality (PQ) and Segmentation Metrics.

Implements exact competition evaluation protocol:
PQ = SQ * RQ where match requires IoU > 0.5.
Provides detailed TP/FP/FN breakdown to diagnose fragmentation and over-merging.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple
import numpy as np


def compute_iou(mask1: np.ndarray, mask2: np.ndarray) -> float:
    """Calculate Intersection over Union (IoU) between two binary boolean masks."""
    intersection = np.sum(mask1 & mask2)
    if intersection == 0:
        return 0.0
    union = np.sum(mask1 | mask2)
    if union == 0:
        return 0.0
    return float(intersection) / float(union)


def compute_dice(mask1: np.ndarray, mask2: np.ndarray) -> float:
    """Calculate Sørensen–Dice coefficient between two binary boolean masks."""
    intersection = np.sum(mask1 & mask2)
    total = np.sum(mask1) + np.sum(mask2)
    if total == 0:
        return 1.0 if intersection == 0 else 0.0
    return float(2.0 * intersection) / float(total)


def panoptic_quality(
    pred_instances: Sequence[np.ndarray],
    gt_instances: Sequence[np.ndarray],
    iou_threshold: float = 0.5,
) -> Dict[str, float]:
    """Calculate Panoptic Quality (PQ), Segmentation Quality (SQ), and Recognition Quality (RQ).

    Args:
        pred_instances: List of 2D boolean masks for predicted filaments.
        gt_instances: List of 2D boolean masks for ground truth filaments.
        iou_threshold: Minimum IoU to qualify as a match (strictly 0.5 per standard PQ).

    Returns:
        Dict with keys: 'pq', 'sq', 'rq', 'tp', 'fp', 'fn', 'mean_dice'.
    """
    n_pred = len(pred_instances)
    n_gt = len(gt_instances)

    # Edge cases
    if n_pred == 0 and n_gt == 0:
        return {"pq": 1.0, "sq": 1.0, "rq": 1.0, "tp": 0, "fp": 0, "fn": 0, "mean_dice": 1.0}
    if n_pred == 0:
        return {"pq": 0.0, "sq": 0.0, "rq": 0.0, "tp": 0, "fp": 0, "fn": n_gt, "mean_dice": 0.0}
    if n_gt == 0:
        return {"pq": 0.0, "sq": 0.0, "rq": 0.0, "tp": 0, "fp": n_pred, "fn": 0, "mean_dice": 0.0}

    # Bipartite matching based on IoU > threshold
    # Since threshold >= 0.5, each ground-truth can match at most ONE prediction
    iou_matrix = np.zeros((n_pred, n_gt), dtype=np.float32)
    for p_idx, p_mask in enumerate(pred_instances):
        for g_idx, g_mask in enumerate(gt_instances):
            iou_matrix[p_idx, g_idx] = compute_iou(p_mask, g_mask)

    matched_pred = set()
    matched_gt = set()
    iou_sum = 0.0
    dice_sum = 0.0
    tp_count = 0

    # Match greedily in descending order of IoU
    matches = []
    for p_idx in range(n_pred):
        for g_idx in range(n_gt):
            score = iou_matrix[p_idx, g_idx]
            if score > iou_threshold:
                matches.append((score, p_idx, g_idx))

    # Sort descending
    matches.sort(key=lambda x: x[0], reverse=True)

    for score, p_idx, g_idx in matches:
        if p_idx not in matched_pred and g_idx not in matched_gt:
            matched_pred.add(p_idx)
            matched_gt.add(g_idx)
            iou_sum += score
            dice_sum += compute_dice(pred_instances[p_idx], gt_instances[g_idx])
            tp_count += 1

    fp_count = n_pred - tp_count
    fn_count = n_gt - tp_count

    sq = iou_sum / tp_count if tp_count > 0 else 0.0
    denominator = tp_count + 0.5 * fp_count + 0.5 * fn_count
    rq = tp_count / denominator if denominator > 0 else 0.0
    pq = sq * rq
    mean_dice = dice_sum / tp_count if tp_count > 0 else 0.0

    return {
        "pq": float(pq),
        "sq": float(sq),
        "rq": float(rq),
        "tp": int(tp_count),
        "fp": int(fp_count),
        "fn": int(fn_count),
        "mean_dice": float(mean_dice),
    }
