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
echo -e "\n🟡 Starting [ACTION]" >> WORK_LOG.md
```

### Step 2: Run JudgeGuard Pre-Check

```bash
python3 judge_guard.py "Start [ACTION]"
```

### Step 3: Evaluate Verdict

- **EXIT 0 (PASSED):** Proceed to execution.
- **EXIT 1 (BLOCKED):** STOP, fix issues, return to Step 1.

### Step 4: Execute the Action

Perform the planned, surgical operation.

### Step 5: Update Work Log

```bash
echo -e "✅ Completed [ACTION]" >> WORK_LOG.md
```

### Step 6: Post-Check

```bash
python3 judge_guard.py "Verify [ACTION] Complete"
```

### Step 7: Git Commit

```bash
git add . && git commit -m "checkpoint: [ACTION]"
```
