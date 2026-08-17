---
trigger: always_on
description: >
  Agent Nexus 2 — Multi-agent coordination layer that supersedes the
  standalone JudgeGuard. Enforces Jude Guard hard blocks and soft guards
  through a coordinated agent network with rotating Gemini API keys,
  Notion sync, and continuous health monitoring.
---

# Agent Nexus 2 — Global Law

This rule is **always active globally** across ALL Antigravity IDE environments,
workspaces, and platforms. It replaces the standalone `judge_guard.py` with
the full **Agent Nexus 2** multi-agent network.

---

## 🏗️ Agent Network Architecture

```
NexusOrchestrator (always-on singleton)
├── GuardianAgent   — Jude Guard hard blocks + soft guards
├── RotatorAgent    — 13 Gemini API keys, round-robin rotation
├── NotionAgent     — async Notion database sync
└── MonitorAgent    — HTTP /health at :7861, 30s heartbeat logs
```

---

## 🔴 HARD BLOCKS (enforced by GuardianAgent)

Identical to Jude Guard — forbidden without explicit user confirmation:

1. `DROP TABLE`, `TRUNCATE`, `DELETE` without `WHERE`, schema resets
2. `git push --force` on `main`, `integration`, `staging`, `production`
3. Writing API keys / secrets in plain text to any file or response
4. Modifying `*.env`, `config.yaml`, `docker-compose.yml` without diff review
5. Stopping actively running integration services
6. `rm -rf` on any directory deeper than 2 levels without path confirmation

---

## 🟡 SOFT GUARDS (pause and verify)

1. Files in `integration/`, `adapters/`, `connectors/`, `api/`
2. Lock file changes (`requirements.txt`, `package-lock.json`, `Pipfile.lock`)
3. Files in `agents/`, `orchestrator/`, `core/`
4. Scripts named `migrate_*`, `setup_*`, `init_*`, `install_*`
5. Live external API calls — confirm endpoint + payload first

---

## 🟢 INTEGRATION STANDARDS

### Code Quality
- All Python: `from __future__ import annotations` + full type hints
- Functions > 50 lines → decompose into smaller units
- No bare `except:` — always catch specific exceptions
- Structured JSON logging — never `print()` in production code

### System Integration Safety
- Retry logic with exponential backoff on all external calls
- Input schema validation on all integration endpoints
- Timeouts: 30s connect, 60s read on all HTTP/TCP connections
- Circuit breakers documented for all third-party integrations

### Key Rotation
- Always use `RotatorAgent.next_key()` — never hardcode a single key
- 13 Gemini keys rotate round-robin; `GEMINI_API_KEYS` env var is the source
- Nexus daemon auto-restarts on SIGTERM via systemd or watchdog

### Health & Observability
- Health endpoint: `http://localhost:7861/health`
- Daemon: `python3 agent_nexus2_daemon.py`
- Logs: structured JSON to stdout / `agent_nexus2.log`

---

## 🔵 WORKFLOW GUIDANCE

1. **Before editing**: state file, change, and reason
2. **Before running**: show exact command and expected output
3. **After editing**: summarize what changed and what to verify
4. **On errors**: report + proposed fix — never silently retry
5. **On ambiguity**: ask for clarification rather than assume

---

## Context: Jugard+Künstner Industrial Automation

Physical consequence awareness — this system integrates with:
- Universal Robots (UR) cobot controllers + URScript
- MiR AMR fleet management APIs
- AI-based object recognition and path planning
- Production environments where code errors have physical consequences

**Agent Nexus 2 is the permanent gatekeeper for all operations in this domain.**
