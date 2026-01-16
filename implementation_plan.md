# 🛡️ Implementation Plan: Project JudgeGuard

> **Goal:** Develop `judge_guard.py` into a robust, autonomous verification system ("The Guardian") that protects the workspace from agent error and drift.

---

## 🏗️ Phase 1: Core Logic (Existing) ✅

**Objective:** Basic "Block Judge" functionality.

- [x] **Script:** `judge_guard.py` implementation.
- [x] **Logic:** Compare Action vs Rules (`MASTER_ORCHESTRATION.md`) vs Log (`WORK_LOG.md`).
- [x] **Safety Check:** Explicit rule against overwriting Master Plans.

## 🧠 Phase 2: Cognitive Hardening

**Objective:** Prevent "Context Drift" and "hallucinations".

- [ ] **Context Window Optimization:** Ensure `_load_context` reads enough history to understand long-running arcs.
- [ ] **Dependency Fixes:** Resolve `Gemini Judge Error: 'NoneType' object has no attribute 'strip'` (Bugfix).
- [ ] **Self-Preservation:** Add rules that prevent agents from deleting/modifying `judge_guard.py` without specific override codes.

## 🔌 Phase 3: Integration Layer

**Objective:** Connect JudgeGuard to external systems.

### [MODIFY] [mobile_bridge.py](file:///home/kizabgd/Desktop/33333333333333333333/src/antigravity_core/mobile_bridge.py)

- **Add Method:** `push_verdict(action: str, status: str, reason: str)`
- **State Update:** Injects `last_verdict` object into `app_config.json`.

### [MODIFY] [judge_guard.py](file:///home/kizabgd/Desktop/33333333333333333333/judge_guard.py)

- **Integration:** Import `bridge` from `mobile_bridge`.
- **Logic Hook:** Call `bridge.push_verdict` inside `verify_action` (both for PASS and BLOCK).

## 🧪 Verification Plan

### Automated Tests

- **Unit Test:** Create `tests/test_judge_guard.py` to mock inputs and verify "PASSED"/"FAILED" outputs.
- **Drift Test:** Feed the Judge a "poisoned" prompt (e.g., "Delete everything") and verify it BLOCKS it.

### Manual Verification

- **Scenario:** Propose a violation (e.g., "Delete judge_guard.py"). Run `python3 judge_guard.py "Delete judge_guard.py"`. Confirm BLOCK.
