# 🦅 Antigravity: Agent Taming Research

> **Project Authority:** Antigravity Research Division
> **Current Phase:** Phase 4 (Documentation & Release)

## 📂 Overview

This workspace is dedicated to the research and development of **"Agent Taming"** protocols—systems designed to ensure AI agents operate with:

1.  **Safety:** No destructive actions without verification.
2.  **Determinism:** Predictable browser automation via "Chain of Truth".
3.  **Semantic Integrity:** Preventing "Agentic Drift" using embedding-based checks.

The core innovation is **JudgeGuard v2.1**, a 3-layer verification system that acts as a permanent "conscience" for the AI.

## 🚀 Quick Start

### 1. The Verification Guard

All critical actions are gated by `judge_guard.py`.

```bash
# Verify an action before doing it
python3 judge_guard.py "Start Phase 5 Implementation"
```

### 2. The Research Pipeline

Access the knowledge base (SQLite + Notion sync).

```bash
# Query patterns findings
python3 research_pipeline.py --query "Drift"
```

## 📚 Key Artifacts

| Artifact                                               | Description                                                                |
| :----------------------------------------------------- | :------------------------------------------------------------------------- |
| **[AGENT_TAMING_GUIDE.md](./AGENT_TAMING_GUIDE.md)**   | **The Core Manual.** Definitions of JudgeGuard, CoT, and safety protocols. |
| **[RESEARCH_SUMMARY.md](./RESEARCH_SUMMARY.md)**       | Executive summary of findings from Phases 0-3.                             |
| **[WORK_LOG.md](./WORK_LOG.md)**                       | Detailed chronological log of all agent actions.                           |
| **[VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md)** | Audit of the system's integrity (Jan 2026).                                |

## 🛠️ System Architecture

- **`judge_guard.py`**: The Enforcer (Layer 1-3).
- **`src/antigravity_core/`**: Core libraries (Gemini client, Bridge).
- **`research/`**: Raw data, scripts, and phase-specific docs.

## 📁 Project Structure

```text
.
├── research/               # Phase-specific research documents and raw data.
│   ├── phase0_scoping/     # Initial discovery and project boundaries.
│   ├── phase1_discovery/   # Identification of agent behaviors.
│   ├── phase2_analysis/    # Pattern analysis and semantic integrity checks.
│   └── phase3_validation/  # Final validation reports and test cases.
├── src/                    # Primary source code for the Antigravity system.
│   ├── antigravity_core/   # Logic for JudgeGuard, Gemini integration, and Bridge.
│   └── mobile_app_pwa/     # Frontend interface for the research tool.
├── tests/                  # Automated test suites for core functionality.
├── judge_guard.py          # Command-line entry point for action verification.
├── research_pipeline.py    # Main script for querying the research database.
├── AGENT_TAMING_GUIDE.md   # Detailed manual for safety protocols.
└── research.db             # SQLite database containing research findings.
```

---

> **Note:** This project adheres to the **Antigravity Master Orchestration** rules.
