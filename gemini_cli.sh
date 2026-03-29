#!/bin/bash
# Gemini CLI Wrapper for Antigravity

ACTION=$1
if [ -z "$ACTION" ]; then
    echo "Usage: gemini '<action>'"
    exit 1
fi

# 1. Update WORK_LOG.md (Mandatory Rule)
# Ensure a newline before appending to prevent corrupted log entries
echo -e "\n🟡 Starting $ACTION" >> WORK_LOG.md

# 2. Run JudgeGuard
# Using python3 from PATH instead of hardcoded absolute paths
python3 judge_guard.py "$ACTION"
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ Action Approved by Gemini (JudgeGuard)"
else
    echo "🛑 Action Rejected by Gemini (JudgeGuard)"
    # Cleanup failed start entry if needed or mark as failed
    echo -e "🛑 Failed $ACTION" >> WORK_LOG.md
    exit 1
fi
