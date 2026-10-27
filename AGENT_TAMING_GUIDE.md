# 🎯 Agent Taming: Advanced Control & Verification Guide

> **Project Authority:** Antigravity Research Division
> **Status:** ✅ Verified & Released (Phase 4)
> **Focus:** Reliable, deterministic, and safe AI agent behavior.

## 📂 Overview

This guide represents the culmination of research into agent control, focusing on eliminating **"Agentic Drift"** and ensuring deterministic interactions in browser environments.

**See Also:**

- [README.md](./README.md) - Project Entry Point
- [RESEARCH_SUMMARY.md](./RESEARCH_SUMMARY.md) - Key Findings & Metrics

---

## 🏛️ The Verification Architecture (JudgeGuard v2.1)

JudgeGuard v2.1 uses a 3-Layer Verification Model + 3 Phase 1.1 upgrades.

### Layer 1: Tool & Context Enforcement

- **Purpose:** Blocking dangerous commands and ensuring the correct tool is used for the current phase.
- **Rule:** In Phases 0 and 1 (Research), `run_command` is **FORBIDDEN**; the Browser Agent is mandatory.

### Layer 2: Live Thought Streaming

- **Purpose:** Observability. Every verdict is streamed to the Mobile Bridge before execution.
- **Implementation:** `bridge.push_verdict()` sends a signal before every PASSED/FAILED decision.

### Layer 3: Semantic Drift Scoring ✅ IMPLEMENTED

- **Purpose:** Measuring the semantic deviation of every action against the "Golden Snapshot".
- **Metric:** `drift_score` (0.0 - 1.0). Hard limit: **0.40** (Gemini), **0.75** (offline heuristic).
- **Self-Healing:** ✅ `retry_with_guidance()` — if an action fails, the Judge returns structured feedback
  enabling the Actor to revise and resubmit (max 2 retries, zero mock).
- **Ground Truth Manifest:** ✅ `_get_ground_truth_manifest()` — re-injects PROJECT_ESSENCE +
  CONTINUITY.md Active Goal into every Layer 3 prompt, preventing context rot across long sessions.

---

## 🌐 Browser "Chain of Truth" (CoT) Loop

For reliable browser automation, the agent must follow a 5-step cycle:

1. **Observe & Anchor:** Before clicking, find stable elements (not just selectors).
2. **Predict:** What is expected after the action? (e.g., URL change, new modal).
3. **Act:** Execute the interaction.
4. **Verify State:** Is the prediction correct? If not -> Error State.
5. **Visual Confirmation:** Use a screenshot for final validation (Multimodal CoT).

---

## 🛠️ Implementation Blueprints

### 1. Drift Detector Snippet

```python
def check_drift(action, essence):
    prompt = f"Does '{action}' drift from '{essence}'? Reply with score."
    # ... logic from drift_prototype.py
```

### 2. Self-Healing Loop

```python
while attempt < max_attempts:
    result = actor.act(context)
    if judge.verify(result):
       return result
    context['feedback'] = judge.get_reason()
```

---

## 🏁 Conclusion

Agent Taming is not about restriction, but **empowerment**. By providing clear boundaries, we enable agents to operate at full power within a safe and predictable framework.

> **Final Verdict:** Verified & Documented.
