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
printf '\n🟡 QWEN: Starting %s at %s\n' "$ACTION" "$(date -Is)" >> WORK_LOG.md

# 2. Hard Security Verification (Layer 00)
ACTION_LOWER=${ACTION,,}
read -r -a ACTION_TOKENS <<< "$ACTION"
BLOCKED=false
if [[ "$ACTION_LOWER" == *sudo* ]]; then
    BLOCKED=true
fi
for ((i = 0; i < ${#ACTION_TOKENS[@]}; i++)); do
    if [[ "${ACTION_TOKENS[i],,}" == "chmod" ]]; then
        for ((j = i + 1; j < ${#ACTION_TOKENS[@]} && j <= i + 3; j++)); do
            if [[ "${ACTION_TOKENS[j],,}" == *r* && "${ACTION_TOKENS[j],,}" == -* ]]; then
                for ((k = j + 1; k < ${#ACTION_TOKENS[@]} && k <= j + 2; k++)); do
                    if [[ "${ACTION_TOKENS[k]}" == "777" ]]; then BLOCKED=true; fi
                done
            fi
        done
    fi
    if [[ "${ACTION_TOKENS[i],,}" == "rm" ]]; then
        recursive=false
        force=false
        j=$((i + 1))
        while ((j < ${#ACTION_TOKENS[@]})) && [[ "${ACTION_TOKENS[j]}" == -* ]]; do
            flags=${ACTION_TOKENS[j],,}
            [[ "$flags" == *r* || "$flags" == *recursive* ]] && recursive=true
            [[ "$flags" == *f* || "$flags" == *force* ]] && force=true
            j=$((j + 1))
        done
        if $recursive && $force && ((j < ${#ACTION_TOKENS[@]})); then
            case "${ACTION_TOKENS[j]}" in
                /|~|\$HOME|\$HOME/\*|/\*|~/*) BLOCKED=true ;;
            esac
        fi
    fi
done
if $BLOCKED; then
    echo "🛑 QWEN BLOCK: Dangerous command pattern detected."
    printf '🛑 QWEN: Blocked %s\n' "$ACTION" >> WORK_LOG.md
    exit 1
fi

echo "✅ QWEN: Local security check passed."

# 3. Call JudgeGuard verification
python3 judge_guard.py "QWEN: $ACTION"
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ Action Approved by Qwen + JudgeGuard"
    printf '✅ QWEN: Completed %s\n' "$ACTION" >> WORK_LOG.md
    exit 0
else
    echo "🛑 Action Rejected by JudgeGuard"
    printf '🛑 QWEN: Rejected %s\n' "$ACTION" >> WORK_LOG.md
    exit 1
fi
