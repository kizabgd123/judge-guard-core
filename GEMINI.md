# JudgeGuard Core — Workspace GEMINI.md

## Project Overview
**judge-guard-core** is a security-enforcement system for AI agents combining a locally-running
JudgeGuard verification engine with Auth0 Token Vault for scoped API authorization.
Architecture: `User Intent → Guardian Agent → JudgeGuard (local) → Auth0 Token Vault → API`

---

## Mandatory Rules (Always Active)

### Zero-Simulation Law
- **NEVER** mock, simulate, or fake any execution (no dummy `deploy`, no fake tokens).
- All operations must be real or explicitly fail-safed to offline queues.

### Pre-Action Verification Gate
Before any critical operation or deployment, run:
```bash
python3 judge_guard.py "<Action Description>"
```
Gate must PASS before proceeding.

### Work Log Traceability
- Log `🟡 Starting <Action>` to `WORK_LOG.md` before starting.
- Log `✅ Completed <Action>` to `WORK_LOG.md` on success.

### Master Constitution
All agents must read and follow `~/.gemini/MASTER_ORCHESTRATION.md`.
See: `.agent/rules/MASTER_LINK.md`

---

## Code Style

### Python
- Style: PEP 8, enforced
- Docstrings: Google-style (`Args:`, `Returns:`, `Raises:`)
- Type hints: Required on all public functions
- Tests: `pytest`, files in `tests/` mirroring `src/` structure
- No globals — use dependency injection

### JavaScript / TypeScript (PWA)
- Path: `src/mobile_app_pwa/`
- Tests: Vitest, files in `src/test/`
- Style: ES modules, async/await preferred over callbacks
- No `var` — use `const`/`let` only
- Test command: `npm run test:gate:kit`

---

## Quality Gates (Run in Order)

```bash
# 1. Secrets scan (run first, always)
npm run gate:secrets

# 2. Build check
npm run build

# 3. Full test suite
npm run test:gate:kit

# 4. JudgeGuard pre-action verification (critical ops only)
python3 judge_guard.py "<Action>"
```

**No deploy without all gates green.**

---

## Directory Structure

```
src/
  antigravity_core/     ← Guardian agent core (guardian_agent.py)
  mobile_app_pwa/       ← PWA frontend
    src/test/           ← Vitest test files
judge_guard.py          ← JudgeGuard verification engine
WORK_LOG.md             ← Mandatory traceability log
.cm/CONTINUITY.md       ← Session working memory (cm-continuity)
.cm/context-bus.json    ← Skill chain context bus
.agent/skills/          ← 53 Antigravity skills (3 workspace + 50 cm-*)
.agent/workflows/       ← /pre-action-verification, /verify_action
```

---

## Active Skills (Key)

| Skill | Use When |
|-------|---------|
| `cm-continuity` | Read at session start, update at session end |
| `cm-quality-gate` | Before any deploy or completion claim |
| `cm-safe-deploy` | Setting up deployment pipelines |
| `cm-guardian-runtime` | Destructive command freeze checks |
| `cm-tdd` | Writing new tests |
| `cm-debugging` | Diagnosing failures |
| `agent-taming` | Chain of Truth, Drift Score, Self-Healing |

Use `/pre-action-verification` or `/verify_action` slash commands before major ops.

---

## Security
- Secrets: `.env` only — never committed
- Run `npm run gate:secrets` frequently
- Auth0 tokens: short-lived, minimum-scope, never cached
