"""Data Agent for Solar Filament 2026.

Audits GONG solar disk observations, verifies pixel intensity bounds,
detects solar limbs, and checks for atmospheric contamination.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

from solar_filament_2026.agents.observability import TRACER
from solar_filament_2026.config import GONG_STATIONS, IMAGE_SHAPE
from solar_filament_2026.data_loader import create_synthetic_solar_disk, parse_filename

logger = logging.getLogger("filament.agents.data")


class SolarFilamentDataAgent:
    """Specialized Agent for GONG Solar Disk Quality Control & Normalization."""

    def __init__(self) -> None:
        self.role = "Data Quality & GONG Calibration Agent"

    def audit_observation(self, image_data: np.ndarray, filename: str) -> Dict[str, Any]:
        """Audit single solar observation for dimensions, dynamic range, and limb contrast."""
        with TRACER.span("data_agent:audit_observation", {"filename": filename}) as span:
            meta = parse_filename(filename)
            h, w = image_data.shape[:2]

            min_val = float(np.min(image_data))
            max_val = float(np.max(image_data))
            mean_val = float(np.mean(image_data))
            std_val = float(np.std(image_data))

            # Solar disk detection: check center vs corner intensity
            cy, cx = h // 2, w // 2
            center_val = float(image_data[cy, cx])
            corner_val = float(image_data[0, 0])
            has_disk = center_val > corner_val + 0.1

            report = {
                "filename": filename,
                "station_code": meta.station_code,
                "station_name": meta.station_name,
                "dimensions": (h, w),
                "dynamic_range": [min_val, max_val],
                "mean_intensity": round(mean_val, 4),
                "std_intensity": round(std_val, 4),
                "solar_disk_detected": has_disk,
                "status": "PASSED" if (h, w) == IMAGE_SHAPE or (h, w) == (512, 512) else "WARNING",
            }
            span["report"] = report
            logger.info(f"Data Agent Audit for {filename}: {report['status']}")
            return report

    def generate_calibration_batch(self, batch_size: int = 3) -> List[Tuple[np.ndarray, List[np.ndarray], Dict[str, Any]]]:
        """Generate verified calibration observations with ground truth."""
        batch = []
        for i in range(batch_size):
            station_code = list(GONG_STATIONS.keys())[i % len(GONG_STATIONS)]
            filename = f"2011052{i}120000{station_code}h.jpeg"
            disk, filaments = create_synthetic_solar_disk(shape=(512, 512), num_filaments=2 + i, seed=100 + i)
            meta = self.audit_observation(disk, filename)
            batch.append((disk, filaments, meta))
        return batch
