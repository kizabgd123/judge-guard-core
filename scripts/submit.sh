#!/usr/bin/env bash
# Submit a prediction file to Kaggle Playground Series s6e10
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: ./scripts/submit.sh <path_to_submission.csv> [message]"
    echo "Example: ./scripts/submit.sh submissions/sub_lgb_cv_0.9610.csv 'Baseline LightGBM 5-fold'"
    exit 1
fi

SUB_FILE="$1"
MESSAGE="${2:-Submission via automated pipeline}"

if [ ! -f "$SUB_FILE" ]; then
    echo "Error: File $SUB_FILE does not exist!"
    exit 1
fi

echo "Submitting $SUB_FILE to Kaggle playground-series-s6e10..."
.venv/bin/kaggle competitions submit -c playground-series-s6e10 -f "$SUB_FILE" -m "$MESSAGE"
echo "Checking submission status..."
.venv/bin/kaggle competitions submissions -c playground-series-s6e10
