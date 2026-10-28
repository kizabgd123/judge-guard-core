"""Evaluation Agent for Solar Filament 2026.

Analyzes Panoptic Quality (PQ), DiceScore, fragmentation, and over-merging.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Sequence
import numpy as np

from solar_filament_2026.agents.observability import TRACER
from solar_filament_2026.config import PARAMS
from solar_filament_2026.metrics import panoptic_quality

logger = logging.getLogger("filament.agents.evaluation")


class SolarFilamentEvaluationAgent:
    """Specialized Agent for Competitive Metric Evaluation & Error Diagnosis."""

    def __init__(self) -> None:
        self.role = "Panoptic Quality Evaluation & Error Diagnosis Agent"

    def evaluate_batch(
        self,
        batch_predictions: Sequence[Sequence[np.ndarray]],
        batch_ground_truths: Sequence[Sequence[np.ndarray]],
        image_ids: Sequence[str],
    ) -> Dict[str, Any]:
        """Evaluate a full batch of images, tracking macro PQ and failure modes."""
        with TRACER.span("evaluation_agent:evaluate_batch", {"num_images": len(image_ids)}) as span:
            per_image_results = []
            pq_list = []
            sq_list = []
            rq_list = []
            total_tp = 0
            total_fp = 0
            total_fn = 0

            for preds, gts, img_id in zip(batch_predictions, batch_ground_truths, image_ids):
                res = panoptic_quality(preds, gts, iou_threshold=PARAMS.iou_match_threshold)
                res["image_id"] = img_id
                per_image_results.append(res)
                pq_list.append(res["pq"])
                sq_list.append(res["sq"])
                rq_list.append(res["rq"])
                total_tp += res["tp"]
                total_fp += res["fp"]
                total_fn += res["fn"]

            mean_pq = float(np.mean(pq_list)) if pq_list else 0.0
            mean_sq = float(np.mean(sq_list)) if sq_list else 0.0
            mean_rq = float(np.mean(rq_list)) if rq_list else 0.0

            # Diagnose primary error mode
            if total_fp > 2 * total_fn:
                primary_error = "FRAGMENTATION / FALSE DETECTIONS (High FP penalizing RQ)"
            elif total_fn > 2 * total_fp:
                primary_error = "OVER-MERGING / MISSED FILAMENTS (High FN penalizing RQ)"
            else:
                primary_error = "BALANCED TOPOLOGY (Good alignment between TP and GT)"

            summary = {
                "mean_panoptic_quality": round(mean_pq, 4),
                "mean_segmentation_quality": round(mean_sq, 4),
                "mean_recognition_quality": round(mean_rq, 4),
                "total_true_positives": total_tp,
                "total_false_positives": total_fp,
                "total_false_negatives": total_fn,
                "primary_error_mode": primary_error,
                "per_image": per_image_results,
            }
            span["summary"] = summary
            logger.info(f"Evaluation Agent: Mean PQ = {mean_pq:.4f} (SQ={mean_sq:.4f}, RQ={mean_rq:.4f})")
            return summary
