---
description: Mandatory workflow before executing ANY major action
---

# Pre-Action Verification Workflow (MANDATORY)

**Authority:** MASTER_ORCHESTRATION.md
**Violation:** System HALT

## When to Use

BEFORE executing ANY of:
- Starting a new Phase
- Schema/database changes
- Goal inscription/updates
- Implementation plans
- Deployments
- Major git commits

## Steps

### Step 1: Update Work Log
```bash
echo "🟡 Starting [ACTION]" >> WORK_LOG.md
```

### Step 2: Run JudgeGuard Pre-Check
// turbo
```bash
python3 judge_guard.py "Start [ACTION]"
```

### Step 3: Evaluate Verdict
- EXIT 0 (PASSED): Proceed
- EXIT 1 (BLOCKED): STOP, fix issues, return to Step 1

### Step 4: Execute the Action

### Step 5: Update Work Log
```bash
echo "✅ Completed [ACTION]" >> WORK_LOG.md
```

### Step 6: Post-Check
// turbo
```bash
python3 judge_guard.py "Verify [ACTION] Complete"
```

### Step 7: Git Commit
// turbo
```bash
git add . && git commit -m "checkpoint: [ACTION]"
```
