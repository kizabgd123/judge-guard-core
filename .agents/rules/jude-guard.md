---
trigger: always_on
description: >
  Jugard System Integration safety guardrail. Enforces production-safety
  constraints, destructive-operation prevention, and integration integrity
  checks for the Jugard (J+K) automation system integration workspace.
---

# Jude Guard — Jugard System Integration Guardrail

This rule is **always active** in the `install_jugard_system_integration` workspace.
It enforces safety, stability, and integrity constraints for industrial automation
and system integration work.

---

## 🔴 HARD BLOCKS — Never Do Without Explicit User Confirmation

The following actions are **absolutely forbidden** without explicit written confirmation from the user:

1. **Destructive database operations** — `DROP TABLE`, `TRUNCATE`, `DELETE` without `WHERE`, schema resets.
2. **Force-push to integration branches** — `git push --force` on `main`, `integration`, `staging`, or `production`.
3. **Credential exposure** — Writing API keys, passwords, tokens, or secrets in plain text to any file, log, or response.
4. **Modifying system configuration files** — `*.env`, `config.yaml`, `docker-compose.yml`, infrastructure manifests without a diff review.
5. **Stopping running integration services** — Do NOT kill, restart, or stop services that are actively processing data.
6. **Bulk file deletion** — `rm -rf` on any directory deeper than 2 levels without explicit path confirmation.

**Response on block**: Describe what you were about to do, explain why it is blocked, and ask the user for explicit written approval before proceeding.

---

## 🟡 SOFT GUARDS — Pause and Verify

For the following actions, pause and state your intent clearly before executing:

1. **Modifying integration adapters** — Any file in `integration/`, `adapters/`, `connectors/`, or `api/` must be reviewed aloud before editing.
2. **Changing dependency versions** — Lock file changes (`package-lock.json`, `requirements.txt`, `Pipfile.lock`) require stating what changes.
3. **Editing agent core files** — Files in `agents/`, `orchestrator/`, or `core/` must be edited with caution and tested.
4. **Running migration scripts** — Any script named `migrate_*`, `setup_*`, `init_*`, or `install_*` must be inspected first.
5. **External API calls** — Confirm endpoint, payload, and consequences before making live calls to external systems.

---

## 🟢 INTEGRATION STANDARDS — Always Enforce

### Code Quality
- All new Python code must include type hints (`from __future__ import annotations`).
- Functions longer than 50 lines must be decomposed into smaller units.
- No bare `except:` clauses — always catch specific exceptions.
- Logging must use structured JSON format, never `print()` in production code.

### System Integration Safety
- All external integrations must implement **retry logic** with exponential backoff.
- All integration endpoints must validate input schemas before processing.
- Timeouts must be set on all HTTP/TCP connections (default: 30s connect, 60s read).
- Circuit breakers must be documented when integrating with third-party systems.

### Git Workflow
- Commit messages must follow: `type(scope): description` (e.g., `feat(integration): add Jugard AMR adapter`).
- Never commit directly to `main` — always use feature branches.
- Branch naming: `feature/`, `fix/`, `chore/`, `hotfix/` prefixes required.

### Testing
- New integration code must have at minimum a smoke test before merge.
- Mock external services in unit tests — never call live endpoints in CI.
- Test files must mirror source structure: `tests/` mirrors `agents/`, `api/`, etc.

### Security
- Secrets are loaded exclusively from environment variables — never hardcoded.
- Use `.env.example` files with placeholder values, never real credentials.
- Validate and sanitize all user/external inputs before processing.
- Log only metadata (IDs, timestamps, statuses) — never log PII or credentials.

---

## 🔵 WORKFLOW GUIDANCE

When working in this workspace:

1. **Before editing**: State the file, the change, and the reason.
2. **Before running**: Show the exact command and expected output.
3. **After editing**: Summarize what changed and what to verify.
4. **On errors**: Do NOT silently retry — report the error and proposed fix.
5. **On ambiguity**: Ask for clarification rather than assuming intent.

---

## Context: Jugard System Integration

This workspace integrates with **Jugard+Künstner (J+K)** industrial automation systems, including:
- **Universal Robots (UR)** cobot controllers and URScript interfaces.
- **MiR (Mobile Industrial Robots)** AMR fleet management APIs.
- **AI-based object recognition** and path planning modules.
- **Production environment** systems where errors have physical consequences.

**Physical consequence awareness**: Changes to robot controller code, AMR routing logic, or production orchestration can have real-world physical effects. Apply extra care.
