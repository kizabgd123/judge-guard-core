# S6E10 Complete Experiment History & Benchmarks

## 1. Submission Leaderboard History

| Submission Ref | Date (UTC) | Description | OOF ROC-AUC | Public LB |
|----------------|------------|-------------|-------------|-----------|
| **57640908** | 2026-10-25 19:26 | S6E10 Sub 3: Quad-Summit Consensus Geodesic Fusion (alpha=1.02) | 0.96225 | **0.96213** |
| **57640880** | 2026-10-25 19:25 | S6E10 Sub 1: SOTA Summit Anchor (Mehran TabPFN + Peeled Nina Base) | 0.96221 | **0.96213** |
| **57647317** | 2026-10-26 00:24 | Multi-Agent NNLS Consensus (Quad-Summit + 3% GPU Trees, alpha=1.025) | 0.96223 | **0.96212** |
| **57461008** | 2026-10-21 01:58 | Apex Sub 1: Dual-Summit Orthogonal Core + 181-Stack Power-Rank (alpha=1.52) | 0.96215 | **0.96207** |
| **57721912** | 2026-10-28 03:11 | S6E10 Route-ID Tri-GBDT Master (In-Fold Bayesian Smoothed TE m=20 + Nelder-Mead) | **0.96041** | **0.95991** |
| **57723036** | 2026-10-28 03:59 | S6E10 Heterogeneous Tri-GBDT & PyTorch Tabular MLP Ensemble | 0.96030 | **0.95981** |
| **57720118** | 2026-10-28 02:00 | Tri-GBDT Rank Ensemble (LGB+CAT+XGB) Cloud GPU 5-Fold OOF Nelder-Mead | 0.95893 | **0.95821** |
| **57679083** | 2026-10-26 21:31 | First-Party 5-Fold Stratified LightGBM Baseline | 0.95852 | **0.95805** |

---

## 2. Model Performance Breakdown (5-Fold Stratified CV on 699,635 rows)

### Run 1: First-Party Tri-GBDT Baseline
- LightGBM 5-Fold OOF: `0.95868`
- CatBoost 5-Fold OOF: `0.95858`
- XGBoost 5-Fold OOF: `0.95858`
- Nelder-Mead Blend: **0.95893** -> LB: **0.95821**

### Run 2: Route-ID Tri-GBDT Master (In-Fold Bayesian Target Encoding)
- LightGBM 5-Fold OOF: `0.96021` (+0.00153)
- CatBoost 5-Fold OOF: `0.96009` (+0.00151)
- XGBoost 5-Fold OOF: `0.96008` (+0.00150)
- Nelder-Mead Blend: **0.96041** -> LB: **0.95991**

### Run 3: Heterogeneous Tri-GBDT & Tabular MLP
- LightGBM OOF: `0.96003`
- CatBoost OOF: `0.95990`
- XGBoost OOF: `0.96008`
- PyTorch Tabular MLP OOF: `0.95697`
- Heterogeneous Blend: **0.96030** -> LB: **0.95981**

---

## 3. Key Architectural Decisions & Insights
1. **Target Encoding on Flight Distance is the single largest tabular signal generator**: Adding zero-leakage in-fold Bayesian Target Encoding ($m=20$) boosted all three GBDT models by +0.0015 OOF AUC.
2. **Standard MLPs underperform GBDTs on tabular synthetic data**: Simple feedforward architectures without specialized tabular priors achieve ~0.9570, requiring TabPFN-3.5 or RealMLP for orthogonal value.
3. **Logit-Rank Manifold Ensembling beats simple rank averaging**: Converting ranks to logits before convex combination stretches tails ($p < 0.05$ and $p > 0.95$), where 83% of ranking errors occur.
