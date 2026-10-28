"""NotebookLM Knowledge Vault Interface.

Provides metadata and programmatic helpers for interacting with the
canonical NotebookLM notebook holding MAGFiLO and GONG solar physics research.
"""

from __future__ import annotations

from typing import Dict, Any

NOTEBOOK_ID = "840e8dc8-e1bc-482a-b85d-13d906bcd064"
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/840e8dc8-e1bc-482a-b85d-13d906bcd064"
NOTEBOOK_TITLE = "Solar Filament Segmentation Challenge 2026 — Research Base & Experiment Vault"

VAULT_SOURCES = [
    {
        "id": "90c9f2ed-e217-4537-8af6-37e29ee2bd0e",
        "title": "MAGFiLO_benchmark_specifications.md",
        "type": "domain_spec",
    },
    {
        "id": "52f8ae67-29d2-4564-81cd-cff8850a4aea",
        "title": "GONG_H_alpha_observatory_stations.md",
        "type": "observatory_physics",
    },
    {
        "id": "7faa45b3-24a6-47a2-92de-57bfcea5e2fe",
        "title": "Panoptic_Quality_formulation_and_penalties.md",
        "type": "evaluation_math",
    },
    {
        "id": "f5d7a84b-cf72-4fc3-b30f-1adf5f0903d1",
        "title": "CPU_optimization_and_zero_gpu_manifest.md",
        "type": "compute_policy",
    },
    {
        "id": "9dfdeb2e-68d6-4122-8933-07cb37b46e5d",
        "title": "experiment_log.md",
        "type": "experiment_vault",
    },
]


def get_vault_metadata() -> Dict[str, Any]:
    """Return canonical NotebookLM vault configuration."""
    return {
        "notebook_id": NOTEBOOK_ID,
        "notebook_url": NOTEBOOK_URL,
        "title": NOTEBOOK_TITLE,
        "sources_count": len(VAULT_SOURCES),
        "sources": VAULT_SOURCES,
    }
