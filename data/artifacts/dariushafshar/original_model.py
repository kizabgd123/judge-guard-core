#!/usr/bin/env python3
"""The original-only model for Kaggle Playground S6E10 (airline passenger satisfaction).

Two models fitted on the 129,880 rows of Arseniy Shutko's CC0 "Airline Satisfaction Data"
(original_aligned.csv in this dataset) and on nothing else. No competition row and no
competition label was used to fit them. Score any frame that has train.csv's 21 feature
columns and use the two outputs as features:

    ogp_xgb_d8   logit of an XGBoost classifier, depth 8, 600 trees
    ogp_lgb      raw score (logit) of LightGBM, mean of 3 seeds, 800 rounds each

Use them as FEATURES. Boosting from them (LightGBM init_score) was measured and costs AUC.

In a notebook:

    import sys; sys.path.append(DATASET_DIR)      # the folder that holds this file
    from original_model import score
    feats = score(train)                          # DataFrame, same index as train

From a shell:

    python original_model.py --input train.csv --output train_ogp.csv
    python original_model.py --refit --out-dir .  # re-fit the four model files from original_aligned.csv

score() loads the fitted model files that sit next to this script. If your XGBoost or
LightGBM cannot read them (a much older version, say), it re-fits the same recipe from
original_aligned.csv in memory, says so, and carries on (about a minute on 10 CPU cores,
longer on fewer).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

TARGET = "satisfaction"
NUMS = ["Age", "Flight Distance", "Departure Delay in Minutes", "Arrival Delay in Minutes"]
RATINGS = ["Inflight wifi service", "Departure/Arrival time convenient", "Ease of Online booking",
           "Gate location", "Food and drink", "Online boarding", "Seat comfort",
           "Inflight entertainment", "On-board service", "Leg room service", "Baggage handling",
           "Checkin service", "Cleanliness"]
CATS = ["Gender", "Customer Type", "Type of Travel", "Class"]
RAW = NUMS + RATINGS + CATS                      # the model's input columns, in this order

# Text columns become integer codes in sorted order of their levels (the levels of the
# original and of the competition files are the same strings).
LEVELS = {
    "Gender": ["Female", "Male"],
    "Customer Type": ["Loyal Customer", "disloyal Customer"],
    "Type of Travel": ["Business travel", "Personal Travel"],
    "Class": ["Business", "Eco", "Eco Plus"],
}

XGB_PARAMS = dict(n_estimators=600, learning_rate=0.05, max_depth=8, subsample=0.8,
                  colsample_bytree=0.5, tree_method="hist", random_state=0)
LGB_PARAMS = dict(objective="binary", learning_rate=0.03, num_leaves=63, min_child_samples=20,
                  feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, verbose=-1)
LGB_ROUNDS = 800
LGB_SEEDS = (0, 1, 2)

XGB_FILE = "original_model_xgb_d8.json"
LGB_FILES = [f"original_model_lgb_seed{s}.txt" for s in LGB_SEEDS]
ORIGINAL_FILE = "original_aligned.csv"


def _say(msg: str) -> None:
    print(f"[original_model] {msg}", file=sys.stderr, flush=True)


def encode(df: pd.DataFrame) -> pd.DataFrame:
    """The 21 input columns as numbers, in the order the models were fitted on."""
    missing = [c for c in RAW if c not in df.columns]
    if missing:
        raise KeyError(f"frame lacks {missing}; it needs train.csv's 21 feature columns")
    X = pd.DataFrame(index=df.index)
    for c in NUMS + RATINGS:
        X[c] = pd.to_numeric(df[c], errors="raise").astype("float64")
    for c in CATS:
        s = df[c].astype("object")
        codes = pd.Categorical(s, categories=LEVELS[c]).codes.astype("float64")
        bad = s.notna().to_numpy() & (codes < 0)
        if bad.any():
            raise ValueError(f"{c!r} has levels the model never saw: "
                             f"{sorted(set(s[bad].astype(str)))[:5]}")
        codes[s.isna().to_numpy()] = np.nan
        X[c] = codes
    return X[RAW]


def _label(s: pd.Series) -> np.ndarray:
    m = s.astype(str).str.strip().str.lower().map({"true": 1, "false": 0, "1": 1, "0": 0})
    if m.isna().any():
        raise ValueError(f"unexpected {TARGET} values: {sorted(set(s.astype(str)))[:5]}")
    return m.astype(int).to_numpy()


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit(original: pd.DataFrame | None = None, n_jobs: int | None = None):
    """Fit the recipe on the original rows. Returns (xgb Booster, [lgb Booster x3])."""
    import lightgbm as lgb
    import xgboost as xgb
    if original is None:
        original = pd.read_csv(HERE / ORIGINAL_FILE)
    n_jobs = n_jobs or os.cpu_count()
    X, y = encode(original), _label(original[TARGET])
    t0 = time.time()
    m = xgb.XGBClassifier(**XGB_PARAMS, n_jobs=n_jobs)
    m.fit(X, y)
    boosters = []
    for seed in LGB_SEEDS:
        p = dict(LGB_PARAMS, seed=seed, num_threads=n_jobs)
        boosters.append(lgb.train(p, lgb.Dataset(X, y), LGB_ROUNDS))
    _say(f"fitted on {len(X):,} original rows in {time.time() - t0:.0f}s "
         f"(xgboost {xgb.__version__}, lightgbm {lgb.__version__})")
    return m.get_booster(), boosters


def save(models, out_dir: Path) -> None:
    xb, lbs = models
    out_dir.mkdir(parents=True, exist_ok=True)
    xb.save_model(str(out_dir / XGB_FILE))
    for b, f in zip(lbs, LGB_FILES):
        b.save_model(str(out_dir / f))


def load(model_dir: Path | str = HERE):
    """Read the four fitted files; re-fit in memory if this XGBoost/LightGBM cannot."""
    import lightgbm as lgb
    import xgboost as xgb
    model_dir = Path(model_dir)
    try:
        xb = xgb.Booster()
        xb.load_model(str(model_dir / XGB_FILE))
        lbs = [lgb.Booster(model_file=str(model_dir / f)) for f in LGB_FILES]
        return xb, lbs
    except Exception as e:   # version mismatch or missing file: same recipe, fitted here
        _say(f"could not read the fitted files ({type(e).__name__}: {e}); "
             f"re-fitting the same recipe from {ORIGINAL_FILE}")
        return fit(pd.read_csv(model_dir / ORIGINAL_FILE))


_CACHE: dict = {}


def score(df: pd.DataFrame, model_dir: Path | str = HERE) -> pd.DataFrame:
    """ogp_xgb_d8 and ogp_lgb (both logits) for every row of df, same index."""
    import xgboost as xgb
    key = str(Path(model_dir).resolve())
    if key not in _CACHE:
        _CACHE[key] = load(model_dir)
    xb, lbs = _CACHE[key]
    X = encode(df)
    out = pd.DataFrame(index=df.index)
    out["ogp_xgb_d8"] = _logit(xb.predict(xgb.DMatrix(X)))
    out["ogp_lgb"] = np.mean([b.predict(X.to_numpy(), raw_score=True) for b in lbs], axis=0)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, help="a CSV with train.csv's feature columns")
    ap.add_argument("--output", type=Path, help="where to write id + the two features")
    ap.add_argument("--refit", action="store_true", help="re-fit the model files from the original")
    ap.add_argument("--out-dir", type=Path, default=HERE, help="where --refit writes the files")
    a = ap.parse_args()
    if a.refit:
        save(fit(pd.read_csv(HERE / ORIGINAL_FILE)), a.out_dir)
        _say(f"wrote {XGB_FILE} and {len(LGB_FILES)} LightGBM files to {a.out_dir}")
    if a.input:
        df = pd.read_csv(a.input)
        f = score(df)
        if "id" in df.columns:
            f.insert(0, "id", df["id"].to_numpy())
        f.to_csv(a.output or sys.stdout, index=False)
    if not (a.refit or a.input):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
