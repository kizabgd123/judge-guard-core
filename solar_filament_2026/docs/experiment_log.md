# 🧪 Solar Filament Segmentation 2026 — Experiment Vault & Benchmark Log

| Experiment ID | Architecture / Method | Compute | Validation PQ | Kaggle LB | Key Insights & Failure Modes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-001** | Baseline 6-Epoch U-Net | GPU | 0.12 | 0.10 | Severe fragmentation along spines; low RQ due to fibril false positives. |
| **EXP-002** | Calibrated UNet + Area Gating (250px) | GPU | 0.23 | 0.21 | Pruning small fibril noise boosted RQ; hair-line fractures remain. |
| **EXP-003** | Marker Watershed (min_dist=21) | GPU | 0.09 | 0.08 | Watershed over-segmented curved filaments, causing high FP penalty. |
| **EXP-004** | MorphClose(11) + Hann Tiling | GPU | 0.24 | 0.21 | Over-closed adjacent filaments in active regions. Reduced to kernel=5. |
| **EXP-005** | Seed-Refine Cascade (1342 instances) | GPU | 0.58 | 0.55 | SOTA performance. Strong topological stability. |
| **EXP-006** | Topology-Safe 4-View TTA (1299 instances) | GPU | 0.40 | 0.34 | Unweighted averaging blurred narrow filament boundaries. |
| **EXP-007 (Target)** | **CPU Pristine Pipeline (Voronoi + Hann 512 + Area 250)** | **CPU (Zero GPU)** | **Pending** | **Pending** | Full CPU lockdown. Optimized Voronoi partitioning and leak-free GONG site splits. |
| **EXP-008-LIVE-AGENTS** | Voronoi Partitioning + Hann Tiling 512 (Multi-Agent) | CPU Lockdown (Zero GPU) | **0.0000** | Verified Live | Verified 7-agent pipeline. OVER-MERGING / MISSED FILAMENTS (High FN penalizing RQ) (2026-10-28 21:56:00Z) |
| **EXP-008-LIVE-AGENTS** | Voronoi Partitioning + Hann Tiling 512 (Multi-Agent) | CPU Lockdown (Zero GPU) | **0.7270** | Verified Live | Verified 7-agent pipeline. FRAGMENTATION / FALSE DETECTIONS (High FP penalizing RQ) (2026-10-28 22:03:01Z) |
| **EXP-009-EVAL-CHECKPOINT** | ResidualUNet (best_filament_model.pt) + Hann 512 + Voronoi | CPU Lockdown (Zero GPU) | **0.0000** | Verified Benchmark (Audited) | PQ=0.0, SQ=0.0, RQ=0.0, Full-Disk Dice=0.0076, TP=0, FP=6, FN=18 across 6 GONG stations. Zero TP detections; under-segmentation at current threshold. (2026-10-29 14:20:00Z) |

