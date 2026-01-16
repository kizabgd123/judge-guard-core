# 🧠 Master Research Plan: JudgeGuard (Autonomous Verification)

> **Project:** JudgeGuard (`judge_guard.py`)
> **Vision:** A self-contained, incorruptible "Guardian" that enforces project rules and sanity-checks agent actions before execution.

---

## 🔬 Phase 0: The Problem (Scoping)
**Why do we need JudgeGuard?**
- **Agent Drift:** Agents tend to forget "Master Plans" and focus only on the immediate task (as seen in the "Implementation Plan Overwrite" incident).
- **Context Loss:** Long conversations lead to forgotten rules.
- **Security:** Agents have `run_command` access; a "sudo" layer is needed.

**Hypothesis:** A stateless, rigorous "Judge" script that re-reads the *entire* Constitution (`MASTER_ORCHESTRATION.md`) for *every* action can prevent 99% of drift.

---

## 🌎 Phase 1: Verification Architecture (Discovery)
**Concept:** "Constitutional AI" / "Block Judge".
1.  **Input:** Proposed Action (e.g., "Delete Database").
2.  **Context:** Recent Work Log + Immutable Rules.
3.  **Process:** Use a *separate* LLM call (zero-shot) to verdict the action.
4.  **Output:** BLOCK or PASS.

**Key Research Findings:**
- **Separation of Concerns:** The "Doer" (Agent) cannot be the "Judge".
- **Immutable Logs:** The Judge relies on `WORK_LOG.md` as the Source of Truth.

---

## 📱 Phase 2: The Human Interface (Mobile PWA)
**Role of the Mobile App:**
- It is NOT just a "Hello World" app.
- It is the **Judge's Gavel**.
- **Transformation:** The PWA we built (Phases 3-5) will be repurposed to show **Real-Time Verdicts**.
- **Feature:** When JudgeGuard blocks an action, it pushes a notification to the PWA. The User clicks "Override" or "Ack".

---

## 🎯 Strategic Alignment
- **JudgeGuard.py** = The Brain/Backend.
- **Mobile PWA** = The Control Panel.
- **Master Plan** = This document, ensuring we never lose sight of the "Guardian" mission.
