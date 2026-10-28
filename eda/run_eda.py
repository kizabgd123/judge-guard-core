"""
Exploratory Data Analysis (EDA) script for Kaggle Playground Series s6e10.
Analyzes data distributions, missing values, correlations, and outputs eda_report.txt.
"""

import os
import sys
import pandas as pd
import numpy as np

def run_eda(data_dir: str = "data/raw", output_file: str = "eda/eda_report.txt"):
    print("=" * 60)
    print("Running EDA on Kaggle Playground Series s6e10")
    print("=" * 60)

    train_path = os.path.join(data_dir, "train.csv")
    test_path = os.path.join(data_dir, "test.csv")
    sub_path = os.path.join(data_dir, "sample_submission.csv")

    if not os.path.exists(train_path):
        print(f"Error: {train_path} not found!")
        sys.exit(1)

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    sub_df = pd.read_csv(sub_path)

    report_lines = []
    report_lines.append("=== KAGGLE PLAYGROUND SERIES S6E10 - EDA REPORT ===\n")
    report_lines.append(f"Train Shape: {train_df.shape} ({train_df.shape[0]:,} rows, {train_df.shape[1]} cols)")
    report_lines.append(f"Test Shape:  {test_df.shape} ({test_df.shape[0]:,} rows, {test_df.shape[1]} cols)")
    report_lines.append(f"Sample Sub Shape: {sub_df.shape}\n")

    # Target variable analysis
    target_col = "satisfaction"
    target_counts = train_df[target_col].value_counts(dropna=False)
    target_pct = train_df[target_col].value_counts(normalize=True, dropna=False) * 100

    report_lines.append("--- TARGET DISTRIBUTION ('satisfaction') ---")
    for val in target_counts.index:
        report_lines.append(f"  {val}: {target_counts[val]:,} ({target_pct[val]:.2f}%)")
    report_lines.append("")

    # Missing values
    report_lines.append("--- MISSING VALUES (TRAIN vs TEST) ---")
    train_nulls = train_df.isnull().sum()
    test_nulls = test_df.isnull().sum()
    null_cols = sorted(set(train_nulls[train_nulls > 0].index).union(test_nulls[test_nulls > 0].index))
    if not null_cols:
        report_lines.append("  No missing values found in train or test!")
    else:
        for c in null_cols:
            tr_n, tr_p = train_nulls.get(c, 0), train_nulls.get(c, 0) / len(train_df) * 100
            te_n, te_p = test_nulls.get(c, 0), test_nulls.get(c, 0) / len(test_df) * 100
            report_lines.append(f"  {c}: Train {tr_n:,} ({tr_p:.2f}%) | Test {te_n:,} ({te_p:.2f}%)")
    report_lines.append("")

    # Feature categorization
    categorical_cols = [c for c in train_df.columns if train_df[c].dtype == 'object' or c in ['Gender', 'Customer Type', 'Type of Travel', 'Class']]
    survey_cols = [c for c in train_df.columns if any(k in c.lower() for k in ['service', 'comfort', 'boarding', 'wifi', 'food', 'cleanliness', 'booking', 'entertainment', 'convenient', 'location'])]
    numeric_cols = [c for c in train_df.columns if c not in categorical_cols + [target_col, 'id']]

    report_lines.append("--- CATEGORICAL FEATURES ---")
    for c in categorical_cols:
        unique_vals = train_df[c].unique().tolist()
        report_lines.append(f"  {c} ({len(unique_vals)} unique): {unique_vals}")
    report_lines.append("")

    report_lines.append("--- SURVEY FEATURES (0 to 5 ratings) ---")
    report_lines.append(f"  Count of survey features: {len(survey_cols)}")
    report_lines.append(f"  Features: {survey_cols}\n")

    report_lines.append("--- NUMERICAL FEATURES SUMMARY ---")
    for c in ['Age', 'Flight Distance', 'Departure Delay in Minutes', 'Arrival Delay in Minutes']:
        if c in train_df.columns:
            s = train_df[c]
            report_lines.append(f"  {c}: min={s.min()}, mean={s.mean():.2f}, median={s.median()}, max={s.max()}, std={s.std():.2f}")
    report_lines.append("")

    # Target correlations (encoding target as numeric 0/1)
    train_copy = train_df.copy()
    if train_copy[target_col].dtype == bool or set(train_copy[target_col].unique()) == {True, False}:
        train_copy[target_col] = train_copy[target_col].astype(int)
    elif train_copy[target_col].dtype == object:
        train_copy[target_col] = train_copy[target_col].map(lambda x: 1 if str(x).lower() in ['1', 'true', 'satisfied'] else 0)

    numeric_for_corr = [c for c in numeric_cols if c in train_copy.columns]
    corrs = train_copy[numeric_for_corr + [target_col]].corr()[target_col].drop(target_col).sort_values(ascending=False)

    report_lines.append("--- TOP CORRELATIONS WITH TARGET (satisfaction) ---")
    for feat, corr in corrs.items():
        report_lines.append(f"  {feat:35s}: {corr:+.4f}")

    report_content = "\n".join(report_lines)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(report_content)
    print(f"\nReport successfully saved to {output_file}")

if __name__ == "__main__":
    run_eda()
