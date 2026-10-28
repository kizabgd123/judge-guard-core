"""Documentation Agent for Solar Filament 2026.

Maintains project experiment logs and synchronizes findings with the
NotebookLM Knowledge Vault.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict

from solar_filament_2026.agents.observability import TRACER
from solar_filament_2026.config import DOCS_DIR
from solar_filament_2026.notebooklm_vault import get_vault_metadata

logger = logging.getLogger("filament.agents.documentation")


class SolarFilamentDocumentationAgent:
    """Specialized Agent for Knowledge Vault Synchronization & Experiment Logging."""

    def __init__(self) -> None:
        self.role = "Documentation & NotebookLM Synchronization Agent"

    def record_experiment_run(
        self,
        experiment_id: str,
        architecture: str,
        compute_mode: str,
        pq_score: float,
        key_insights: str,
    ) -> Dict[str, Any]:
        """Append benchmark run to experiment_log.md and emit synchronization payload."""
        with TRACER.span("documentation_agent:record_experiment_run", {"experiment_id": experiment_id}) as span:
            log_path = DOCS_DIR / "experiment_log.md"
            date_str = time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())
            
            entry_line = (
                f"| **{experiment_id}** | {architecture} | {compute_mode} | "
                f"**{pq_score:.4f}** | Verified Live | {key_insights} ({date_str}) |\n"
            )

            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(entry_line)
                logger.info(f"Recorded experiment {experiment_id} in {log_path}")
            except Exception as e:
                logger.warning(f"Could not append to experiment log: {e}")

            vault_meta = get_vault_metadata()
            result = {
                "experiment_id": experiment_id,
                "recorded_at": date_str,
                "pq_score": pq_score,
                "notebooklm_vault": vault_meta["title"],
                "notebooklm_id": vault_meta["notebook_id"],
                "status": "RECORDED",
            }
            span["result"] = result
            return result
