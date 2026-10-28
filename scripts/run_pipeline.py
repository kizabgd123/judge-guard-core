"""
End-to-End Orchestrator for Kaggle S6E10 (Predicting Airline Satisfaction).
Coordinates data loading, feature engineering, 5-Fold Tri-GBDT modeling,
Nelder-Mead rank ensembling, and Kaggle submission.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import cfg
from src.data_loader import load_data
from src.features import generate_features
from src.cv import evaluate_auc
from src.models.lgbm_model import train_lgbm_kfold
from src.models.catboost_model import train_catboost_kfold
from src.models.xgboost_model import train_xgboost_kfold
from src.ensemble import optimize_blend_weights, generate_ensemble_predictions
from scripts.submit import validate_submission, submit_to_kaggle

def parse_args():
    parser = argparse.ArgumentParser(description="Run S6E10 Competitive ML Pipeline")
    parser.add_argument("--sample-rows", type=int, default=None, help="Sample rows for dry runs")
    parser.add_argument("--folds", type=int, default=5, help="Number of folds (default: 5)")
    parser.add_argument("--models", nargs="+", default=["lgb", "cat", "xgb"], choices=["lgb", "cat", "xgb"], help="Models to train")
    parser.add_argument("--skip-submit", action="store_true", help="Skip Kaggle CLI submission")
    parser.add_argument("--skip-cat", action="store_true", help="Convenience flag to skip CatBoost if desired")
    return parser.parse_args()

def run_pipeline():
    args = parse_args()
    selected_models = args.models
    if args.skip_cat and "cat" in selected_models:
        selected_models.remove("cat")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(cfg.SUBMISSIONS_DIR, exist_ok=True)

    print("=" * 70)
    print("✈️ KAGGLE S6E10 END-TO-END COMPETITIVE ML PIPELINE")
    print(f"Timestamp: {timestamp}")
    print(f"Models: {[m.upper() for m in selected_models]}")
    print(f"Folds: {args.folds} | Sample: {args.sample_rows or 'Full (700k)'}")
    print("=" * 70)

    # 1. Load Data
    print("\n[1/5] Loading datasets...")
    train_raw, test_raw, sub_template = load_data(nrows=args.sample_rows)
    print(f"  Train records: {len(train_raw):,}")
    print(f"  Test records:  {len(test_raw):,}")

    # 2. Feature Engineering
    print("\n[2/5] Running Feature Engineering Engine...")
    train_feat, test_feat, feature_names = generate_features(train_raw, test_raw)
    print(f"  ✅ Generated {len(feature_names)} features.")

    X = train_feat[feature_names]
    y = train_feat[cfg.TARGET_COL]
    X_test = test_feat[feature_names]

    # 3. Model Training
    print("\n[3/5] Training GBDT Architectures (5-Fold Stratified CV)...")
    oof_dict = {}
    test_dict = {}
    scores_dict = {}

    for model_name in selected_models:
        if model_name == "lgb":
            oof_p, test_p, oof_auc, fold_aucs = train_lgbm_kfold(
                X, y, X_test, n_splits=args.folds, verbose=True
            )
        elif model_name == "cat":
            oof_p, test_p, oof_auc, fold_aucs = train_catboost_kfold(
                X, y, X_test, n_splits=args.folds, verbose=True
            )
        elif model_name == "xgb":
            oof_p, test_p, oof_auc, fold_aucs = train_xgboost_kfold(
                X, y, X_test, n_splits=args.folds, verbose=True
            )

        oof_dict[model_name] = oof_p
        test_dict[model_name] = test_p
        scores_dict[model_name] = {
            "overall_auc": oof_auc,
            "fold_aucs": fold_aucs,
            "std": float(np.std(fold_aucs))
        }

        # Save individual model submission
        ind_sub = sub_template.copy()
        ind_sub[cfg.TARGET_COL] = test_p
        ind_sub_file = cfg.SUBMISSIONS_DIR / f"sub_{model_name}_cv_{oof_auc:.5f}_{timestamp}.csv"
        ind_sub.to_csv(ind_sub_file, index=False)
        print(f"  💾 Saved {model_name.upper()} submission -> {ind_sub_file.name}")

    # 4. Ensembling & Calibration
    print("\n[4/5] Optimizing Nelder-Mead Rank Ensemble...")
    oof_list = [oof_dict[m] for m in selected_models]
    test_list = [test_dict[m] for m in selected_models]

    if len(selected_models) > 1:
        weights, blend_auc = optimize_blend_weights(oof_list, y.values)
        print(f"⭐ Optimal Nelder-Mead Ensemble OOF ROC AUC: {blend_auc:.5f}")
        for m, w in zip(selected_models, weights):
            print(f"   - {m.upper()} Weight: {w:.4f} (CV: {scores_dict[m]['overall_auc']:.5f})")

        ensemble_test_preds = generate_ensemble_predictions(test_list, weights, use_ranking=True)
    else:
        weights = np.array([1.0])
        blend_auc = scores_dict[selected_models[0]]["overall_auc"]
        ensemble_test_preds = test_list[0]

    # Save ensemble submission
    ens_sub = sub_template.copy()
    ens_sub[cfg.TARGET_COL] = ensemble_test_preds
    ens_sub_file = cfg.SUBMISSIONS_DIR / f"sub_ensemble_cv_{blend_auc:.5f}_{timestamp}.csv"
    ens_sub.to_csv(ens_sub_file, index=False)
    print(f"\n🏆 Final Blended Submission Saved: {ens_sub_file}")

    # 5. Validation and Submission
    print("\n[5/5] Validating & Kaggle CLI Submission...")
    expected_rows = len(sub_template) if args.sample_rows else 299844
    validate_submission(ens_sub_file, expected_rows=expected_rows)
    print("  ✅ Submission passed all schema & distribution checks.")

    if not args.skip_submit and args.sample_rows is None:
        message = f"Tri-GBDT Rank Blend (LGB+CAT+XGB) CV={blend_auc:.5f} ({timestamp})"
        submit_to_kaggle(ens_sub_file, message=message)
    elif args.skip_submit:
        print("  ℹ️ Submission skipped by --skip-submit flag.")
    else:
        print("  ℹ️ Submission skipped because sample run was performed.")

    # Save experiment report
    summary = {
        "timestamp": timestamp,
        "models": selected_models,
        "sample_rows": args.sample_rows,
        "model_scores": scores_dict,
        "ensemble_weights": {m: float(w) for m, w in zip(selected_models, weights)},
        "ensemble_auc": float(blend_auc),
        "submission_file": str(ens_sub_file)
    }
    with open(cfg.SUBMISSIONS_DIR / f"experiment_summary_{timestamp}.json", "w") as f:
        json.dump(summary, f, indent=2)

    return summary

if __name__ == "__main__":
    run_pipeline()
