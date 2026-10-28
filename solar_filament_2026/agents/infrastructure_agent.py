"""Infrastructure Agent for Solar Filament 2026.

Audits cloud and local compute resources, enforcing zero-GPU Kaggle lockdown
and validating kernel packages.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from solar_filament_2026.agents.observability import TRACER
from solar_filament_2026.config import KAGGLE_CPU_DIR

logger = logging.getLogger("filament.agents.infrastructure")


class SolarFilamentInfrastructureAgent:
    """Specialized Agent for Compute Quota Governance & Kernel Deployment Audit."""

    def __init__(self) -> None:
        self.role = "Infrastructure & Zero-GPU Compliance Agent"

    def audit_compute_environment(self) -> Dict[str, Any]:
        """Perform pre-flight verification on Kaggle kernel metadata and CPU readiness."""
        with TRACER.span("infrastructure_agent:audit_compute_environment") as span:
            meta_path = KAGGLE_CPU_DIR / "kernel-metadata.json"
            if not meta_path.exists():
                raise FileNotFoundError(f"Missing kernel metadata at {meta_path}")

            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            is_gpu_disabled = meta.get("enable_gpu") is False
            is_tpu_disabled = meta.get("enable_tpu") is False
            is_offline_ready = meta.get("enable_internet") is False
            competition = meta.get("competition_sources", [])

            report = {
                "kernel_slug": meta.get("id"),
                "zero_gpu_compliance": is_gpu_disabled,
                "zero_tpu_compliance": is_tpu_disabled,
                "offline_inference_ready": is_offline_ready,
                "bound_competition": competition,
                "status": "APPROVED" if (is_gpu_disabled and is_tpu_disabled and is_offline_ready) else "BLOCKED",
            }
            span["report"] = report
            logger.info(f"Infrastructure Agent Audit: {report['status']}")
            return report
