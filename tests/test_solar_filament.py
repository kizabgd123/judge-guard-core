"""Comprehensive Unit & Integration Test Suite for Solar Filament 2026.

Verifies:
1. Zero-GPU configuration adherence across config and Kaggle kernel metadata.
2. GONG observation filename parsing and station mapping.
3. Hann-window sliding tiling and seamless canvas reconstruction.
4. COCO RLE codec roundtripping with area preservation.
5. Voronoi instance partitioning and spine bridging.
6. Mathematical accuracy of Panoptic Quality (PQ = SQ * RQ) and edge cases.
7. Agent research inquiry and OpenTelemetry trace logging.
8. NotebookLM knowledge vault metadata integrity.
"""

import json
from pathlib import Path
import numpy as np
import pytest

from solar_filament_2026.config import (
    COMPETITION_ID,
    ENABLE_GPU,
    GONG_STATIONS,
    IMAGE_SHAPE,
    KAGGLE_CPU_DIR,
    PARAMS,
)
from solar_filament_2026.data_loader import (
    create_synthetic_solar_disk,
    load_solar_image,
    parse_filename,
)
from solar_filament_2026.feature_tiling import HannTiler, create_2d_hann_window
from solar_filament_2026.metrics import compute_dice, compute_iou, panoptic_quality
from solar_filament_2026.notebooklm_vault import get_vault_metadata
from solar_filament_2026.postprocess_topology import (
    mask_to_rle,
    morphological_close_hairline,
    rle_to_mask,
    voronoi_partition_instances,
)
from solar_filament_2026.agents.observability import TRACER
from solar_filament_2026.agents.research_agent import SolarFilamentResearchAgent
from solar_filament_2026.agents.orchestrator import FilamentPipelineOrchestrator


def test_zero_gpu_compliance():
    """Verify that GPU is strictly disabled across all configurations."""
    assert ENABLE_GPU is False, "ENABLE_GPU must be strictly False"

    metadata_path = KAGGLE_CPU_DIR / "kernel-metadata.json"
    assert metadata_path.exists(), "Kaggle CPU kernel-metadata.json must exist"

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["enable_gpu"] is False, "kernel-metadata.json must have enable_gpu: false"
    assert meta["enable_tpu"] is False, "kernel-metadata.json must have enable_tpu: false"
    assert meta["enable_internet"] is False, "kernel-metadata.json must have enable_internet: false"
    assert "filament-segmentation-2026" in meta["competition_sources"]


def test_gong_filename_parsing():
    """Verify GONG station extraction from standard observation filenames."""
    filename = "20110120105534Ch.jpeg"
    meta = parse_filename(filename)

    assert meta.station_code == "C"
    assert "Cerro Tololo" in meta.station_name
    assert meta.year == 2011
    assert meta.month == 1
    assert meta.day == 20
    assert meta.hour == 10
    assert meta.minute == 55
    assert meta.second == 34


def test_synthetic_solar_disk():
    """Verify synthetic solar disk and ground-truth filament generator."""
    disk, filaments = create_synthetic_solar_disk(shape=(256, 256), num_filaments=2, seed=123)
    assert disk.shape == (256, 256)
    assert disk.min() >= 0.0 and disk.max() <= 1.0
    assert len(filaments) > 0
    for f in filaments:
        assert f.shape == (256, 256)
        assert f.dtype == bool
        assert np.sum(f) > 0


def test_hann_tiling_reconstruction():
    """Verify that Hann-window tiling reconstructs constant canvas seamlessly."""
    tiler = HannTiler(image_shape=(256, 256), tile_size=128, overlap=32)
    canvas = np.ones((256, 256), dtype=np.float32)

    tiles = tiler.extract_tiles(canvas)
    assert len(tiles) > 1

    tile_preds = [t[0] for t in tiles]
    recon = tiler.reconstruct(tile_preds)

    assert recon.shape == (256, 256)
    # Check that reconstructed canvas is close to original constant value
    np.testing.assert_allclose(recon, 1.0, atol=1e-3)


def test_rle_roundtrip():
    """Verify COCO RLE encoding and decoding preserves mask shape and area."""
    mask = np.zeros((100, 100), dtype=bool)
    mask[20:50, 30:70] = True
    expected_area = np.sum(mask)

    rle_str = mask_to_rle(mask)
    assert isinstance(rle_str, str)
    assert len(rle_str) > 0

    decoded = rle_to_mask(rle_str, height=100, width=100)
    assert decoded.shape == (100, 100)
    assert np.array_equal(mask, decoded)
    assert np.sum(decoded) == expected_area


def test_morphological_closing():
    """Verify morphological close bridges hairline fractures."""
    mask = np.zeros((50, 50), dtype=bool)
    mask[20, 10:20] = True
    # 2px gap
    mask[20, 22:32] = True

    closed = morphological_close_hairline(mask, kernel_size=5)
    # The gap should now be bridged
    assert closed[20, 20] is True or closed[20, 20] == 1
    assert closed[20, 21] is True or closed[20, 21] == 1


def test_voronoi_partitioning():
    """Verify Voronoi instance partitioning separates distinct probability peaks."""
    prob = np.zeros((100, 100), dtype=np.float32)
    # Peak 1
    prob[20:35, 20:35] = 0.9
    # Peak 2
    prob[65:80, 65:80] = 0.9

    instances = voronoi_partition_instances(
        prob_map=prob,
        prob_threshold=0.4,
        seed_threshold=0.7,
        min_distance=5,
        min_area=20,
    )

    assert len(instances) == 2
    for inst in instances:
        assert inst.shape == (100, 100)
        assert np.sum(inst) >= 20


def test_panoptic_quality_math():
    """Verify Panoptic Quality calculation on identical, disjoint, and partial masks."""
    m1 = np.zeros((100, 100), dtype=bool)
    m1[10:30, 10:30] = True

    m2 = np.zeros((100, 100), dtype=bool)
    m2[50:70, 50:70] = True

    # 1. Perfect Match
    perfect = panoptic_quality([m1, m2], [m1, m2])
    assert perfect["pq"] == pytest.approx(1.0)
    assert perfect["sq"] == pytest.approx(1.0)
    assert perfect["rq"] == pytest.approx(1.0)
    assert perfect["tp"] == 2
    assert perfect["fp"] == 0
    assert perfect["fn"] == 0

    # 2. Missed Ground Truth (1 False Negative)
    missed = panoptic_quality([m1], [m1, m2])
    # tp=1, fp=0, fn=1 -> rq = 1 / (1 + 0.5) = 2/3 = 0.6667
    assert missed["tp"] == 1
    assert missed["fn"] == 1
    assert missed["rq"] == pytest.approx(1.0 / 1.5)
    assert missed["pq"] == pytest.approx(1.0 / 1.5)

    # 3. Spurious Prediction (1 False Positive)
    spurious = panoptic_quality([m1, m2], [m1])
    assert spurious["tp"] == 1
    assert spurious["fp"] == 1
    assert spurious["rq"] == pytest.approx(1.0 / 1.5)

    # 4. Empty Cases
    empty = panoptic_quality([], [])
    assert empty["pq"] == 1.0


def test_research_agent_and_observability(tmp_path):
    """Verify Research Agent execution and OpenTelemetry tracing."""
    agent = SolarFilamentResearchAgent()
    res = agent.research_topic("voronoi instance partition")

    assert res["topic"] == "voronoi instance partition"
    assert len(res["findings"]) > 0
    assert "Voronoi" in res["findings"][0]["principle"]

    # Verify trace span logging
    with TRACER.span("test_verification_span", {"test_key": "test_val"}) as span:
        span["inner_key"] = 123
    assert TRACER.trace_log_path.exists()


def test_notebooklm_vault_metadata():
    """Verify NotebookLM vault metadata configuration."""
    vault = get_vault_metadata()
    assert vault["notebook_id"] == "840e8dc8-e1bc-482a-b85d-13d906bcd064"
    assert "Solar Filament" in vault["title"]
    assert vault["sources_count"] >= 5
