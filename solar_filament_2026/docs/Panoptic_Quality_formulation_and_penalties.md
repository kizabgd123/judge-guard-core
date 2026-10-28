# 📐 Panoptic Quality (PQ) Metric Formulation & Structural Penalties

## 1. Mathematical Formulation
Panoptic Quality (PQ) is the unified evaluation metric for instance and semantic segmentation (Kirillov et al., 2019), adopted by the **Solar Filament Segmentation Challenge 2026**.

For a set of predicted segments $P$ and ground-truth segments $G$:
A predicted segment $p \in P$ and ground-truth segment $g \in G$ are matched as a **True Positive ($TP$)** if and only if:
$$\text{IoU}(p, g) > 0.5$$

Due to the mathematical property of $\text{IoU} > 0.5$, each ground truth segment can match with at most one predicted segment, establishing a unique bipartite matching.

The remaining unmatched predictions are **False Positives ($FP$)**:
$$FP = \{p \in P \mid \forall g \in G, \text{IoU}(p, g) \le 0.5\}$$

The remaining unmatched ground-truth filaments are **False Negatives ($FN$)**:
$$FN = \{g \in G \mid \forall p \in P, \text{IoU}(p, g) \le 0.5\}$$

### Decomposition of PQ:
$$PQ = \underbrace{\frac{\sum_{(p, g) \in TP} \text{IoU}(p, g)}{|TP|}}_{\text{Segmentation Quality (SQ)}} \times \underbrace{\frac{|TP|}{|TP| + \frac{1}{2}|FP| + \frac{1}{2}|FN|}}_{\text{Recognition Quality (RQ)}}$$

## 2. Asymmetric Error Penalties in Solar Filaments
1. **Fragmentation Penalty (Catastrophic)**:
   - If a ground-truth filament is broken into two halves by a detector, at best one half might reach $\text{IoU} > 0.5$ (often neither does!).
   - If one half matches: it generates $1\times TP$ with low $\text{IoU}$ plus $1\times FP$ for the second fragment.
   - If neither half matches: it generates $1\times FN$ and $2\times FP$, severely penalizing $RQ$.
2. **Over-Merging Penalty**:
   - If two nearby distinct filaments are merged into a single predicted blob:
   - The combined prediction cannot have $\text{IoU} > 0.5$ with both filaments. At best, it matches one and leaves the other as $FN$, while diluting the matched $\text{IoU}$.
3. **Small Spurious Noise**:
   - Every small false detection (e.g. sunspots or dark chromospheric fibrils with $\text{area} < 250\text{ px}$) acts as an unmatched $FP$, decreasing the denominator $|TP| + \frac{1}{2}|FP| + \frac{1}{2}|FN|$.

## 3. Algorithmic Solution
- **Morphological Closing**: Use a small kernel ($5\times 5$) to bridge $1\text{--}2\text{ px}$ hairline spine fractures.
- **Euclidean Distance-Transform Voronoi Partitioning**: Instead of naive connected components or unconstrained DBSCAN, use distance-transform ridge detection to split necked mergers while preserving filament continuity.
- **Area Gating**: Hard prune instances with $\text{area} < 250\text{ px}$ to suppress fibril noise.
