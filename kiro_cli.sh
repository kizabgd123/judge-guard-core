#!/bin/bash
# Kiro CLI Wrapper

ACTION=$1
if [ -z "$ACTION" ]; then
    echo "Usage: ./kiro_cli.sh <action>"
    exit 1
fi

echo "--- KIRO INTERVENTION: Initiating ---"
echo -e "\n🟡 KIRO: Starting $ACTION" >> WORK_LOG.md

python3 judge_guard.py "KIRO: $ACTION"
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ KIRO: Action Approved"
else
    echo "🛑 KIRO: Action Blocked"
    exit 1
fi
