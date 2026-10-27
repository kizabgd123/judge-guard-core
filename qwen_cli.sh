#!/bin/bash
# Qwen CLI Wrapper for Antigravity - Real Verification Enforcer

ACTION=$1
if [ -z "$ACTION" ]; then
    echo "Usage: qwen '<action>'"
    exit 1
fi

echo "--- QWEN AGENT: Verifying Intent & Security ---"
echo "🔍 Action: $ACTION"

# 1. Update WORK_LOG.md (Mandatory Traceability Rule)
echo -e "\n🟡 QWEN: Starting $ACTION" >> WORK_LOG.md

# 2. Hard Security Verification (Layer 00)
if [[ "$ACTION" == *"sudo"* || "$ACTION" == *"rm -rf /"* || "$ACTION" == *"chmod -R 777"* ]]; then
    echo "🛑 QWEN BLOCK: Dangerous command pattern detected."
    echo -e "🛑 QWEN: Blocked $ACTION" >> WORK_LOG.md
    exit 1
fi

echo "✅ QWEN: Local security check passed."

# 3. Call JudgeGuard verification
python3 judge_guard.py "QWEN: $ACTION"
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ Action Approved by Qwen + JudgeGuard"
    echo -e "✅ QWEN: Completed $ACTION" >> WORK_LOG.md
    exit 0
else
    echo "🛑 Action Rejected by JudgeGuard"
    echo -e "🛑 QWEN: Rejected $ACTION" >> WORK_LOG.md
    exit 1
fi
