"""Multi-Agent System Orchestrator.

Coordinates research, data preprocessing, Hann-window tiling,
topology-safe Voronoi partitioning, and Panoptic Quality evaluation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from solar_filament_2026.agents.observability import TRACER
from solar_filament_2026.agents.research_agent import SolarFilamentResearchAgent
from solar_filament_2026.config import PARAMS
from solar_filament_2026.feature_tiling import HannTiler
from solar_filament_2026.metrics import panoptic_quality
from solar_filament_2026.postprocess_topology import mask_to_rle, voronoi_partition_instances

logger = logging.getLogger("filament.agents.orchestrator")


class FilamentPipelineOrchestrator:
    """Master Orchestrator integrating all agents and pipeline stages."""

    def __init__(self) -> None:
        self.researcher = SolarFilamentResearchAgent()
        self.tiler = HannTiler(
            image_shape=(2048, 2048),
            tile_size=PARAMS.hann_tile_size,
            overlap=PARAMS.hann_tile_overlap,
        )

    def run_research_inquiry(self, topic: str) -> Dict[str, Any]:
        """Dispatch research agent inquiry and log telemetry span."""
        with TRACER.span("orchestrator:run_research_inquiry", {"topic": topic}):
            return self.researcher.research_topic(topic)

    def process_probability_canvas(
        self,
        prob_canvas: np.ndarray,
        image_id: str = "test_image",
    ) -> List[Tuple[str, str]]:
        """Execute postprocessing on a full 2048x2048 probability map.
        
        Returns:
            List of (filament_id, segmentation_rle) tuples ready for submission CSV.
        """
        with TRACER.span("orchestrator:process_probability_canvas", {"image_id": image_id}) as span:
            instances = voronoi_partition_instances(
                prob_map=prob_canvas,
                prob_threshold=PARAMS.prob_threshold,
                seed_threshold=PARAMS.seed_prob_threshold,
                min_distance=PARAMS.voronoi_min_distance,
                min_area=PARAMS.min_instance_area,
                morph_kernel=PARAMS.morph_close_kernel_size,
            )

            records = []
            for inst_idx, mask in enumerate(instances):
                filament_id = f"{image_id}_{inst_idx}"
                rle_str = mask_to_rle(mask)
                records.append((filament_id, rle_str))

            span["detected_instances"] = len(records)
            return records

    def evaluate_instances(
        self,
        predicted_masks: List[np.ndarray],
        ground_truth_masks: List[np.ndarray],
    ) -> Dict[str, float]:
        """Evaluate instance segmentations against ground truth."""
        with TRACER.span("orchestrator:evaluate_instances"):
            return panoptic_quality(
                predicted_masks,
                ground_truth_masks,
                iou_threshold=PARAMS.iou_match_threshold,
            )
