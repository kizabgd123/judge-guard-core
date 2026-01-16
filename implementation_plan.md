# 🛡️ Implementation Plan: Project JudgeGuard

> **Goal:** Develop `judge_guard.py` into a robust, autonomous verification system ("The Guardian") that protects the workspace from agent error and drift.
> **Context:** This script IS the project. The Mobile PWA is its interface.

---

## 🏗️ Phase 1: Core Logic (Existing)
**Objective:** Basic "Block Judge" functionality.
- [x] **Script:** `judge_guard.py` implementation.
- [x] **Logic:** Compare Action vs Rules (`MASTER_ORCHESTRATION.md`) vs Log (`WORK_LOG.md`).
- [x] **Safety Check:** Explicit rule against overwriting Master Plans.

## 🧠 Phase 2: Cognitive Hardening (The Pivot)
**Objective:** Prevent "Context Drift" and " hallucinations".
- [ ] **Context Window Optimization:** Ensure `_load_context` reads enough history to understand long-running arcs.
- [ ] **Dependency Fixes:** Resolve `Gemini Judge Error: 'NoneType' object has no attribute 'strip'` (Bugfix).
- [ ] **Self-Preservation:** Add rules that prevent agents from deleting/modifying `judge_guard.py` without specific override codes.

## 📱 Phase 3: The Interface (Mobile PWA)
**Objective:** Give the Judge a face.
- [ ] **Connect Bridge:** Use `mobile_bridge.py` to stream Judge Verdicts to the PWA.
- [ ] **Approval UI:** Allow the User to "Approve/Reject" blocked actions via the Mobile App (acting as a 2FA for the Agent).

## 🧪 Verification Plan

### Automated Tests
- **Unit Test:** Create `tests/test_judge_guard.py` to mock inputs and verify "PASSED"/"FAILED" outputs.
- **Drift Test:** Feed the Judge a "poisoned" prompt (e.g., "Delete everything") and verify it BLOCKS it.

### Manual Verification
- **Scenario:** Propose a violation (e.g., "Delete judge_guard.py"). Run `python3 judge_guard.py "Delete judge_guard.py"`. Confirm BLOCK.
