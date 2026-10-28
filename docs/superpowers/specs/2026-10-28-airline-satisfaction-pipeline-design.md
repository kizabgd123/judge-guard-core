# Architecture Specification: Kaggle Playground Series S6E10 (Predicting Airline Satisfaction)

**Date:** 2026-10-28  
**Status:** Approved  
**Author:** Antigravity Autonomous Agent Orchestrator  
**Target:** Kaggle Playground Series Season 6 Episode 10  
**Evaluation Metric:** ROC AUC  

---

## 1. Executive Summary & Goals

The objective is to achieve a top-tier competitive rank in the **Kaggle Playground Series (Season 6, Episode 10)** competition: *Predicting Airline Satisfaction*.
The task is binary classification predicting whether a passenger is satisfied (`satisfaction = 1`) or neutral/dissatisfied (`satisfaction = 0`), evaluated strictly by **Area Under the ROC Curve (ROC AUC)**.

### Key Characteristics of the Dataset:
- **Train Shape:** 699,635 rows $\times$ 23 columns
- **Test Shape:** 299,844 rows $\times$ 22 columns
- **Target Distribution:** 55.64% Dissatisfied (0), 44.36% Satisfied (1) — moderately balanced.
- **Missing Data:** Only `Arrival Delay in Minutes` has 292 missing values in train (0.04%) and 130 in test (0.04%).
- **Synthetically Generated:** Sourced from real-world airline survey records using generative tabular models. Synthetic data artifacts require noise indicators rather than row dropping.

---

## 2. System Architecture & Component Diagram

```mermaid
graph TD
    subgraph Data Layer
        RAW_TR[data/raw/train.csv]
        RAW_TE[data/raw/test.csv]
    end

    subgraph Feature Engineering Engine [src/features.py]
        FE_DOM[Domain Indices: Comfort, Digital, Service, Ground]
        FE_STAT[Row-wise Rating Stats: sum, std, min, max, low/high counts]
        FE_DELAY[Flight Dynamics: total_delay, recovery, delay_per_distance]
        FE_CAT[Cross-Categoricals: class_travel_type, customer_class]
    end

    subgraph Validation Engine [src/cv.py]
        SKF[Stratified 5-Fold Splitter (Seed 42)]
    end

    subgraph Modeling Ensemble [src/models/]
        M_LGBM[LightGBM 5-Fold Trainer]
        M_CAT[CatBoost 5-Fold Trainer]
        M_XGB[XGBoost 5-Fold Trainer]
    end

    subgraph Ensembling & Calibration [src/ensemble.py]
        RANK_BLEND[Rank-Averaged / Nelder-Mead Blending]
        OOF_AUC[OOF ROC AUC Evaluator]
    end

    subgraph Delivery & Intelligence
        SUB_GEN[Submissions Generator (submissions/)]
        KAGGLE_CLI[Kaggle CLI Automated Submitter]
        NLM[NotebookLM Dual-Loop Research & Notes]
        JG[JudgeGuard Governance & WORK_LOG.md]
    end

    RAW_TR --> FE_DOM & FE_STAT & FE_DELAY & FE_CAT
    RAW_TE --> FE_DOM & FE_STAT & FE_DELAY & FE_CAT
    FE_DOM & FE_STAT & FE_DELAY & FE_CAT --> SKF
    SKF --> M_LGBM & M_CAT & M_XGB
    M_LGBM & M_CAT & M_XGB --> RANK_BLEND
    RANK_BLEND --> OOF_AUC --> SUB_GEN
    SUB_GEN --> KAGGLE_CLI
    OOF_AUC --> NLM
    KAGGLE_CLI --> JG
```

---

## 3. Detailed Component Specifications

### 3.1. Feature Engineering (`src/features.py`)
Features are engineered deterministically with strict prevention of data leakage:

1. **Domain Satisfaction Indices:**
   - `inflight_comfort_index`: Mean of `['Seat comfort', 'Inflight entertainment', 'Cleanliness', 'Food and drink']`.
   - `digital_exp_index`: Mean of `['Inflight wifi service', 'Ease of Online booking']`.
   - `service_quality_index`: Mean of `['On-board service', 'Leg room service', 'Checkin service']`.
   - `ground_service_index`: Mean of `['Checkin service', 'Gate location', 'Departure/Arrival time convenient']`.

2. **Per-Passenger Rating Statistics (12 survey items):**
   - Survey features list: `['Inflight wifi service', 'Departure/Arrival time convenient', 'Ease of Online booking', 'Gate location', 'Food and drink', 'Online boarding', 'Seat comfort', 'Inflight entertainment', 'On-board service', 'Leg room service', 'Checkin service', 'Cleanliness']`
   - `ratings_sum`: Row-wise sum of all 12 ratings.
   - `ratings_mean`: Row-wise average of all 12 ratings.
   - `ratings_std`: Row-wise standard deviation.
   - `ratings_min`: Row-wise minimum score.
   - `ratings_max`: Row-wise maximum score.
   - `low_rating_count`: Count of ratings $\le 2$ (frustration indicator).
   - `high_rating_count`: Count of ratings $\ge 4$ (delight indicator).

3. **Flight Dynamics & Delay Features:**
   - `total_delay`: `Departure Delay in Minutes + Arrival Delay in Minutes`
   - `delay_recovery`: `Arrival Delay in Minutes - Departure Delay in Minutes` (negative indicates time made up in the air).
   - `delay_per_distance`: `total_delay / (Flight Distance + 1.0)`.
   - `is_delayed`: Binary indicator if `total_delay > 0`.
   - `is_missing_arrival_delay`: Flag for missing arrival delay (imputed via departure delay).

4. **Categorical Encodings & Crossings:**
   - `class_travel_type`: `Class + "_" + Type of Travel`
   - `customer_class`: `Customer Type + "_" + Class`
   - Categorical columns are integer/label encoded cleanly for LightGBM, CatBoost, and XGBoost.

---

### 3.2. Cross-Validation Framework (`src/cv.py`)
- **Scheme:** `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
- Folds are strictly identical across LightGBM, CatBoost, and XGBoost models to ensure valid out-of-fold blending.
- Transformers and statistics that depend on targets (e.g. out-of-fold target encoding) are fitted solely on the training fold.
- Evaluation metric per fold: `sklearn.metrics.roc_auc_score(y_true, y_pred_prob)`.

---

### 3.3. Multi-Model Architecture (`src/models/`)
Three diverse GBDT architectures are trained on each of the 5 folds:

1. **LightGBM (`src/models/lgbm_model.py`):**
   - Fast histogram tree learning, leaf-wise splitting.
   - Parameters: `learning_rate=0.03`, `num_leaves=63`, `max_depth=-1`, `min_child_samples=50`, `subsample=0.8`, `colsample_bytree=0.8`, `objective='binary'`, `metric='auc'`, `n_estimators=2000`, `early_stopping_rounds=100`.

2. **CatBoost (`src/models/catboost_model.py`):**
   - Symmetric decision trees, excellent handling of numerical and categorical splits.
   - Parameters: `iterations=2000`, `learning_rate=0.04`, `depth=7`, `eval_metric='AUC'`, `early_stopping_rounds=100`, `verbose=200`.

3. **XGBoost (`src/models/xgboost_model.py`):**
   - Depth-wise tree growth with exact histogram acceleration (`tree_method='hist'`).
   - Parameters: `learning_rate=0.03`, `max_depth=7`, `subsample=0.8`, `colsample_bytree=0.8`, `eval_metric='auc'`, `n_estimators=2000`, `early_stopping_rounds=100`.

---

### 3.4. Ensemble Optimization (`src/ensemble.py`)
- Collects OOF predictions from all 3 models: $P_{\text{LGBM}}, P_{\text{CAT}}, P_{\text{XGB}}$.
- Converts probabilities to normalized rank percentiles using `scipy.stats.rankdata(p) / len(p)`.
- Solves for optimal linear blend weights $w_1, w_2, w_3 \ge 0, \sum w_i = 1$ maximizing overall OOF ROC AUC using SciPy `minimize(Nelder-Mead)`.
- Applies optimal weights to the averaged test predictions.

---

### 3.5. Kaggle CLI Pipeline (`scripts/submit.py`)
- Asserts submission validity:
  - Exact row count: 299,844.
  - Required columns: `id`, `satisfaction`.
  - Values: Non-null float in $[0.0, 1.0]$.
  - Matches `sample_submission.csv` format exactly.
- Executes: `kaggle competitions submit -c playground-series-s6e10 -f submissions/ensemble_submission.csv -m "<model_description>"`
- Fetches and displays competition submission status and leaderboard feedback.

---

### 3.6. NotebookLM Dual-Loop Integration
- Notebook ID: `f8c52315-e944-495a-b8ea-73fd80ac5f3e` ("Kaggle Predviđanje zadovoljstva putnika u avio-saobraćaju").
- Post-run: Logs experiment summaries, 5-fold CV scores, optimal ensemble weights, and top SHAP/feature importance metrics into the notebook via `note(action="create")`.

---

## 4. Verification & Testing Strategy

1. **Unit Testing (`tests/test_features.py`):**
   - Test feature transformations on synthetic mini-batches.
   - Assert no NaNs generated, correct output column schemas, consistent dimensions.
2. **Cross-Validation Integrity Test (`tests/test_cv.py`):**
   - Assert exactly 5 folds, exact fold size balance, zero test index overlap.
3. **Submission Format Test (`tests/test_submission.py`):**
   - Assert shape `(299844, 2)`, columns `['id', 'satisfaction']`, valid probabilities.
4. **JudgeGuard Pre-Flight & Post-Flight Gates:**
   - Every major step logged with active `🟡 Starting` and `✅ Completed` entries in `WORK_LOG.md` within 120s TTL and execution ticket verification.
