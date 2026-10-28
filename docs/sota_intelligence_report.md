# Kaggle S6E10 SOTA Intelligence & Competitive Landscape Report

## 1. Executive Summary
- **Competition:** Kaggle Playground Series Season 6 Episode 10 (`playground-series-s6e10`) — Airline Passenger Satisfaction.
- **Evaluation Metric:** Area Under the ROC Curve (ROC-AUC).
- **Current Standing Horizon:**
  - **Rank 1:** Masaya Kawamata (`0.96437`, submitted 2026-10-28 01:32:01 UTC)
  - **Rank 2:** Ahmet Bugrahan Altunok (`0.96352`)
  - **Rank 3:** nammovuivui (`0.96297`)
  - **Rank 4:** Gray Robertson (`0.96276`)
  - **Open-Source SOTA Masterpiece:** Yuvraj Lamba v15 (`0.96276+`)
  - **Our Historical Summit Anchor:** `0.96213` (Submission Refs 57640880, 57640908, 57647317)
  - **Our Pure First-Party Route-ID Run:** `0.95991` (CV 0.96041)

---

## 2. Competitive Landscape & Top Solutions Matrix

| Rank / Team | Score | Core Architectural Strategy |
|-------------|-------|-----------------------------|
| Masaya Kawamata | **0.96437** | Continuous-Leaf PLR (Piecewise Linear Representation) + Full-Manifold Tabular Foundation Transformers |
| Ahmet Bugrahan Altunok | **0.96352** | Wide Ridge GLM with L-BFGS + Deep Route Feature Engineering + High-Bin GBDT |
| Gray Robertson | **0.96276** | RealMLP (PyTabKit) + CatBoost Ordered CTR + Route Profile Geometry |
| Yuvraj Lamba (v15) | **0.96276+** | 5-Fold Continuous RepLeaf PLR + Teacher Logits + Altunok Wide GLM + Noise-Bounded Manifold Logit Synthesis |
| Consensus Ground-State | **0.96213** | Quad-Summit Geodesic Consensus (TabPFN-3.5 + Peeled Nina Base + GPU Tree Stack) |

---

## 3. The 0.96213 Ceiling vs. The 0.96276 - 0.96437 Breakthrough

### The Constant-Leaf Quantization Trap
Standard GBDT models (LightGBM, XGBoost, CatBoost) partition feature space into hyper-rectangles and assign a single scalar to each terminal leaf.
In the extreme tails of prediction distributions ($p < 0.05$ and $p > 0.95$), where **83.18% of all pairwise ranking errors occur**, thousands of test instances are assigned identical scores.
When evaluated by ROC-AUC (a purely rank-based metric), ties and coarse quantization degrade the curve.

### Breakthrough Mechanisms
1. **Continuous Leaf Interpolation (`RepLeafClassifier` / `TorchPLREncoder`):**
   Fits a localized linear model inside each leaf:
   $$f_l(x) = w_l^T \phi_{\text{PLR}}(x) + b_l$$
   This eliminates discrete leaf step quantization and restores smooth gradient resolution across CTGAN continuous manifolds.

2. **Route Profile Geometry (+0.0020 AUC):**
   `Flight Distance` operates as a discrete Route ID (~3,500 distinct routes). Invariant route features computed over the combined train+test pool:
   - `fd_mean_*` across all 13 survey dimensions
   - `fd_mean_Age` and `fd_count`
   - `fd_share_Class` (business class proportion per route)

3. **Structural Zero-Rating Flags:**
   CTGAN encodes N/A ratings as 0. Explicit zero flags (`{col}_is_zero`, `wifi_0_booking_0`, `food_0_entertainment_0`, `zero_survey_count`) disentangle synthetic artifacts from genuine satisfaction.

4. **Original Data Teacher Model & Empirical Priors:**
   Arseniy Shutko's 130k real surveys provide `ogp_xgb_d8` and `ogp_lgb` teacher logits + `lookup_long.csv` prior rates (`orig_rate__*`).

5. **Logit-Rank Manifold Tail-Stretching:**
   Transforming percentile ranks into logit space:
   $$z = \ln\left(\frac{r}{1 - r}\right)$$
   followed by simplex ensembling subject to $\sigma(\Delta R) \le 0.00120$ preserves the robust 0.96213 anchor while expanding tail separation.
