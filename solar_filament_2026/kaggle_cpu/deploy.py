"""Deployment & Verification Script for Kaggle CPU Kernel.

Verifies:
1. "enable_gpu" is strictly False.
2. Kernel code_file exists.
3. Provides dry-run validation before pushing.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("filament.deploy")


def verify_cpu_kernel_metadata(metadata_path: Path) -> dict:
    """Strictly assert that GPU and TPU are disabled in Kaggle kernel metadata."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    if meta.get("enable_gpu") is not False:
        raise ValueError(f"VIOLATION: enable_gpu must be False, got {meta.get('enable_gpu')}")

    if meta.get("enable_tpu") is not False:
        raise ValueError(f"VIOLATION: enable_tpu must be False, got {meta.get('enable_tpu')}")

    code_file = metadata_path.parent / meta.get("code_file", "")
    if not code_file.exists():
        raise FileNotFoundError(f"Kernel code file missing: {code_file}")

    logger.info("Kernel metadata verified: strictly CPU-only.")
    return meta


def push_kernel(dry_run: bool = True) -> bool:
    """Validate and optionally push CPU kernel to Kaggle."""
    curr_dir = Path(__file__).resolve().parent
    metadata_path = curr_dir / "kernel-metadata.json"

    meta = verify_cpu_kernel_metadata(metadata_path)
    print(f"✅ Verified CPU Kernel: {meta['id']} (enable_gpu=False)")

    if dry_run:
        print("Dry run complete. Use --push flag to deploy to Kaggle Cloud.")
        return True

    cmd = ["kaggle", "kernels", "push", "-p", str(curr_dir)]
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Push failed: {res.stderr}")
        return False

    print(f"✅ Kernel pushed successfully:\n{res.stdout}")
    return True


if __name__ == "__main__":
    should_push = "--push" in sys.argv
    success = push_kernel(dry_run=not should_push)
    sys.exit(0 if success else 1)
