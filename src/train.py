"""
Main training pipeline script for Kaggle S6E10.
Usage:
  python src/train.py --model lgb --save-submission
  python src/train.py --model all --save-submission
"""

import argparse
import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np

from src.config import cfg
from src.data_loader import load_data
from src.preprocessing import FeatureEngineer
from src.models.baseline import train_kfold_model
from src.models.ensemble import rank_average, optimize_blend

def parse_args():
    parser = argparse.ArgumentParser(description="Train Kaggle S6E10 models")
    parser.add_argument("--model", type=str, default="lgb", choices=["lgb", "xgb", "cat", "all"], help="Model architecture")
    parser.add_argument("--folds", type=int, default=5, help="Number of CV folds")
    parser.add_argument("--nrows", type=int, default=None, help="Sample rows for fast experimentation")
    parser.add_argument("--save-submission", action="store_true", help="Generate submission file")
    return parser.parse_args()

def main():
    args = parse_args()

    print("=" * 60)
    print(f"Kaggle Playground Series S6E10 - Pipeline Execution")
    print(f"Model: {args.model.upper()} | Folds: {args.folds} | Sample: {args.nrows or 'Full'}")
    print("=" * 60)

    # 1. Load data
    print("⏳ Loading raw data...")
    train_raw, test_raw, sub = load_data(nrows=args.nrows)
    print(f"Train shape: {train_raw.shape}, Test shape: {test_raw.shape}")

    # 2. Preprocess & Feature Engineer
    print("⏳ Engineering features...")
    fe = FeatureEngineer()
    train_df, test_df = fe.fit_transform(train_raw, test_raw)
    features = fe.feature_names
    print(f"✅ Generated {len(features)} features: {features[:8]}...")

    X = train_df[features]
    y = train_df[cfg.TARGET_COL]
    X_test = test_df[features]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(cfg.SUBMISSIONS_DIR, exist_ok=True)

    if args.model != "all":
        oof_preds, test_preds, cv_auc, _ = train_kfold_model(
            args.model, X, y, X_test=X_test, n_splits=args.folds
        )

        if args.save_submission and test_preds is not None:
            sub[cfg.TARGET_COL] = test_preds
            sub_file = cfg.SUBMISSIONS_DIR / f"sub_{args.model}_cv_{cv_auc:.5f}_{timestamp}.csv"
            sub.to_csv(sub_file, index=False)
            print(f"💾 Submission saved to: {sub_file}")

    else:
        # Multi-model training and ensembling
        models = ["lgb", "xgb", "cat"]
        oof_dict = {}
        test_dict = {}

        for m in models:
            oof, test_p, cv_score, _ = train_kfold_model(m, X, y, X_test=X_test, n_splits=args.folds)
            oof_dict[m] = oof
            test_dict[m] = test_p

        oof_list = [oof_dict[m] for m in models]
        test_list = [test_dict[m] for m in models]

        # 1. Rank Average Ensemble
        rank_oof = rank_average(oof_list)
        from sklearn.metrics import roc_auc_score
        rank_auc = roc_auc_score(y, rank_oof)
        rank_test = rank_average(test_list)
        print(f"🏆 Rank Average Ensemble OOF ROC-AUC: {rank_auc:.5f}")

        # 2. Optimized Weighted Blend
        blend_oof, blend_test, weights, blend_auc = optimize_blend(oof_list, y.values, test_list)
        print(f"🏆 Optimized Weighted Blend OOF ROC-AUC: {blend_auc:.5f}")
        for m, w in zip(models, weights):
            print(f"   - {m.upper()} weight: {w:.3f}")

        if args.save_submission:
            # Save best ensemble
            sub[cfg.TARGET_COL] = blend_test
            sub_file = cfg.SUBMISSIONS_DIR / f"sub_ensemble_blend_cv_{blend_auc:.5f}_{timestamp}.csv"
            sub.to_csv(sub_file, index=False)
            print(f"💾 Ensemble submission saved to: {sub_file}")

if __name__ == "__main__":
    main()
