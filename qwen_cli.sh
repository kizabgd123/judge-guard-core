#!/bin/bash
# Qwen CLI Wrapper for Antigravity (Mocked for Now)

ACTION=$1
if [ -z "$ACTION" ]; then
    echo "Usage: qwen '<action>'"
    exit 1
fi

echo "--- QWEN AGENT: Verifying Logic ---"
echo "🔍 Checking logic for: $ACTION"

# 1. Update WORK_LOG.md (Consistency with Gemini)
# Ensure a newline before appending to prevent corrupted log entries
echo -e "\n🟡 QWEN: Starting $ACTION" >> WORK_LOG.md

# 2. Logic Check (Simple mock check for now)
if [[ "$ACTION" == *"sudo"* || "$ACTION" == *"rm -rf"* ]]; then
    echo "🛑 QWEN BLOCK: Dangerous command detected."
    echo -e "🛑 QWEN: Blocked $ACTION" >> WORK_LOG.md
    exit 1
fi

echo "✅ QWEN: Action looks safe."

# 3. Call JudgeGuard using python3 from PATH
python3 judge_guard.py "QWEN: $ACTION"
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ Action Approved by Qwen + JudgeGuard"
else
    echo "🛑 Action Rejected by JudgeGuard"
    echo -e "🛑 QWEN: Rejected $ACTION" >> WORK_LOG.md
    exit 1
fi
