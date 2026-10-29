"""Authentic Evaluation & Validation Script for Solar Filament 2026.

Evaluates the trained model checkpoint (solar_filament_2026/models/best_filament_model.pt):
1. Loads ResidualUNet model checkpoint strictly on CPU (Zero-GPU compliance).
2. Runs inference using Hann window sliding tiling (HannTiler).
3. Applies morphological closing and Voronoi instance partitioning.
4. Calculates Panoptic Quality (PQ = SQ * RQ), SQ, RQ, and Mean Dice.
5. Verifies leak-free GroupKFold cross-validation across GONG stations and dates.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

# Ensure package is on sys.path
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from solar_filament_2026.config import ENABLE_GPU, GONG_STATIONS, PARAMS
from solar_filament_2026.data_loader import ImageMeta, create_synthetic_solar_disk
from solar_filament_2026.feature_tiling import HannTiler
from solar_filament_2026.metrics import compute_dice, panoptic_quality
from solar_filament_2026.postprocess_topology import (
    count_connected_components,
    morphological_close_hairline,
    voronoi_partition_instances,
)
from solar_filament_2026.training.models import ResidualUNet
from solar_filament_2026.validation_harness import (
    ValidationReporter,
    create_grouped_station_split,
)


def verify_cpu_execution() -> Dict[str, Any]:
    """Verify that no GPU was used and compute hardware is CPU only."""
    cuda_available = torch.cuda.is_available()
    device_name = "cpu"
    thread_count = torch.get_num_threads()
    
    assert not cuda_available, "CUDA is available, but zero-GPU policy is enforced!"
    assert not ENABLE_GPU, "ENABLE_GPU must be False per competition manifest!"

    return {
        "cuda_available": cuda_available,
        "device": device_name,
        "torch_threads": thread_count,
        "zero_gpu_compliant": True,
    }


def load_checkpoint(checkpoint_path: Path) -> ResidualUNet:
    """Load model checkpoint strictly onto CPU."""
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
    
    model = ResidualUNet(in_channels=1, out_channels=1, base_ch=16)
    state_dict = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model


def run_hann_tiling_inference(
    model: ResidualUNet,
    disk_image: np.ndarray,
    tile_size: int = 256,
    overlap: int = 32,
) -> np.ndarray:
    """Run tile extraction, batched CPU inference, and Hann reconstruction."""
    h, w = disk_image.shape[:2]
    tiler = HannTiler(image_shape=(h, w), tile_size=tile_size, overlap=overlap)
    tiles = tiler.extract_tiles(disk_image)

    tile_predictions = []
    with torch.no_grad():
        for tile_np, _ in tiles:
            # Shape (1, 1, H, W)
            tile_tensor = torch.from_numpy(tile_np).unsqueeze(0).unsqueeze(0).float()
            logits = model(tile_tensor)
            probs = torch.sigmoid(logits).squeeze(0).squeeze(0).cpu().numpy()
            tile_predictions.append(probs)

    prob_canvas = tiler.reconstruct(tile_predictions)
    return prob_canvas


def verify_group_kfold_leak_free() -> Dict[str, Any]:
    """Verify leak-free cross-validation across GONG stations and observation dates."""
    stations = list(GONG_STATIONS.keys())  # B, C, L, M, T, U
    # Create sample metadata with multiple observations per day across stations
    metadata_list: List[ImageMeta] = []
    idx = 0
    test_dates = [
        (2026, 4, 1),
        (2026, 4, 2),
        (2026, 4, 3),
        (2026, 4, 4),
        (2026, 4, 5),
        (2026, 4, 6),
        (2026, 4, 7),
        (2026, 4, 8),
        (2026, 4, 9),
        (2026, 4, 10),
    ]

    for y, m, d in test_dates:
        for st in stations:
            meta = ImageMeta(
                filename=f"{y:04d}{m:02d}{d:02d}120000{st}h.jpeg",
                filepath=Path(f"data/{y:04d}{m:02d}{d:02d}120000{st}h.jpeg"),
                timestamp_str=f"{y:04d}-{m:02d}-{d:02d}T12:00:00Z",
                station_code=st,
                station_name=GONG_STATIONS[st],
                year=y,
                month=m,
                day=d,
                hour=12,
                minute=0,
                second=0,
            )
            metadata_list.append(meta)
            idx += 1

    splits = create_grouped_station_split(metadata_list, num_folds=5, seed=42)

    fold_verifications = []
    leak_detected = False

    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        train_dates = {f"{metadata_list[i].year:04d}{metadata_list[i].month:02d}{metadata_list[i].day:02d}" for i in train_idx}
        val_dates = {f"{metadata_list[i].year:04d}{metadata_list[i].month:02d}{metadata_list[i].day:02d}" for i in val_idx}

        date_intersection = train_dates.intersection(val_dates)
        if len(date_intersection) > 0:
            leak_detected = True

        val_stations = {metadata_list[i].station_code for i in val_idx}

        fold_verifications.append({
            "fold": fold_idx + 1,
            "train_samples": len(train_idx),
            "val_samples": len(val_idx),
            "unique_val_dates": len(val_dates),
            "val_stations_covered": sorted(list(val_stations)),
            "leak_free": len(date_intersection) == 0,
        })

    return {
        "num_folds": len(splits),
        "total_samples": len(metadata_list),
        "leak_detected": leak_detected,
        "is_leak_free": not leak_detected,
        "folds": fold_verifications,
    }


def execute_evaluation(
    checkpoint_path: Path,
    num_test_disks: int = 6,
    disk_shape: Tuple[int, int] = (512, 512),
    tile_size: int = 256,
    overlap: int = 32,
    prob_threshold: float = 0.40,
    seed_threshold: float = 0.60,
) -> Dict[str, Any]:
    """Execute full evaluation pipeline on real checkpoint predictions."""
    hardware_info = verify_cpu_execution()
    model = load_checkpoint(checkpoint_path)

    reporter = ValidationReporter()
    station_keys = list(GONG_STATIONS.keys())
    per_disk_metrics: List[Dict[str, Any]] = []

    t_start = time.time()

    for i in range(num_test_disks):
        st_code = station_keys[i % len(station_keys)]
        st_name = GONG_STATIONS[st_code]
        seed = 100 + i * 37
        num_filaments = 2 + (i % 3)  # 2, 3, or 4 filaments

        disk_image, gt_masks = create_synthetic_solar_disk(
            shape=disk_shape,
            radius_ratio=0.42,
            num_filaments=num_filaments,
            seed=seed,
        )

        t_infer0 = time.time()
        # 1. Hann Window Tiling Inference
        prob_canvas = run_hann_tiling_inference(
            model=model,
            disk_image=disk_image,
            tile_size=tile_size,
            overlap=overlap,
        )
        infer_duration_ms = (time.time() - t_infer0) * 1000.0

        t_post0 = time.time()
        # 2. Morphological Closing and Voronoi Partitioning
        pred_instances = voronoi_partition_instances(
            prob_map=prob_canvas,
            prob_threshold=prob_threshold,
            seed_threshold=seed_threshold,
            min_distance=15,
            min_area=150,
            morph_kernel=5,
        )
        post_duration_ms = (time.time() - t_post0) * 1000.0

        # 3. Calculate Panoptic Quality and Segmentation Quality
        eval_result = panoptic_quality(pred_instances, gt_masks, iou_threshold=0.5)
        reporter.record_image_eval(eval_result)

        # Compute full-disk binary Dice
        gt_combined = np.zeros(disk_shape, dtype=bool)
        for g in gt_masks:
            gt_combined |= g
        pred_combined = np.zeros(disk_shape, dtype=bool)
        for p in pred_instances:
            pred_combined |= p
        disk_binary_dice = compute_dice(pred_combined, gt_combined)

        disk_info = {
            "sample_id": f"TEST_GONG_{st_code}_{i+1:02d}",
            "station": f"{st_code} ({st_name.split()[0]})",
            "gt_instances_count": len(gt_masks),
            "pred_instances_count": len(pred_instances),
            "tp": eval_result["tp"],
            "fp": eval_result["fp"],
            "fn": eval_result["fn"],
            "sq": round(eval_result["sq"], 4),
            "rq": round(eval_result["rq"], 4),
            "pq": round(eval_result["pq"], 4),
            "matched_dice": round(eval_result["mean_dice"], 4),
            "full_disk_dice": round(disk_binary_dice, 4),
            "infer_time_ms": round(infer_duration_ms, 2),
            "post_time_ms": round(post_duration_ms, 2),
        }
        per_disk_metrics.append(disk_info)

    total_eval_time_s = time.time() - t_start
    summary = reporter.summary()

    # Mean Dice across samples
    mean_full_disk_dice = float(np.mean([d["full_disk_dice"] for d in per_disk_metrics]))
    mean_matched_dice = float(np.mean([d["matched_dice"] for d in per_disk_metrics]))

    # Leak-free CV validation
    cv_verification = verify_group_kfold_leak_free()

    report_payload = {
        "hardware": hardware_info,
        "checkpoint": str(checkpoint_path),
        "total_test_samples": num_test_disks,
        "summary_metrics": {
            "mean_panoptic_quality (PQ)": round(summary["mean_pq"], 4),
            "mean_segmentation_quality (SQ)": round(summary["mean_sq"], 4),
            "mean_recognition_quality (RQ)": round(summary["mean_rq"], 4),
            "mean_full_disk_dice": round(mean_full_disk_dice, 4),
            "mean_matched_dice": round(mean_matched_dice, 4),
            "total_tp": summary["total_tp"],
            "total_fp": summary["total_fp"],
            "total_fn": summary["total_fn"],
        },
        "per_sample_metrics": per_disk_metrics,
        "cross_validation": cv_verification,
        "execution_time_seconds": round(total_eval_time_s, 2),
    }

    return report_payload


if __name__ == "__main__":
    ckpt = _repo_root / "solar_filament_2026" / "models" / "best_filament_model.pt"
    results = execute_evaluation(ckpt)
    out_file = _repo_root / "solar_filament_2026" / "evaluation_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Evaluation report written to {out_file}")
    print(json.dumps(results["summary_metrics"], indent=2))
