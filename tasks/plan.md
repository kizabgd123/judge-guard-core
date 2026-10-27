# Implementation Plan: MCP Servers + Hooks + Rules in Antigravity IDE

> **JudgeGuard ticket:** `6dd31500-20e3-4b28-bd15-de4ed3bcaf84`  
> **Drift Score:** 0.15 / 1.00 (PASSED)  
> **Date:** 2026-10-27

## Overview

Instalacija i verifikacija `personalized-service-health` i `sequential-thinking` MCP servera u Antigravity IDE, sa:
1. Aktivnim `hooks.json` koji fizički blokira komande bez JudgeGuard verifikacije
2. Pravilom verifikacije (`always_on`) koje zabranjuje mock testove i lažne tvrdnje
3. Stvarnim testovima koji pokrivaju nove izmene (ne mock testovi staro stanje)
4. Kompletnim `git diff` i Exit Code 0 dokazima pre svake potvrde

## Stanje pre-implementacije (Šta JE konfigurisano)

| Komponenta | Status | Napomena |
|---|---|---|
| `personalized-service-health` u `mcp_config.json` | ✅ POSTOJI | `servicehealth.googleapis.com/mcp` — auth: google_credentials |
| `sequential-thinking` u `mcp_config.json` | ✅ POSTOJI | `npx @modelcontextprotocol/server-sequential-thinking` |
| Tool schemas u `~/.gemini/antigravity-cli/mcp/` | ✅ POSTOJI | `list_project_events.json`, `get_project_event.json`, `sequentialthinking.json` |
| `.agents/rules/verification.md` | ❌ NE POSTOJI | Treba kreirati |
| `.agents/hooks.json` | ❌ NE POSTOJI | Treba kreirati |
| `scripts/verify_command_safety.py` | ❌ NE POSTOJI | Treba kreirati |
| `scripts/log_audit.py` | ❌ NE POSTOJI | Treba kreirati |
| Stvarni testovi za hook i pravilo | ❌ NE POSTOJI | Treba kreirati |

## Architecture Decisions

- **Hooks putanja:** `.agents/hooks.json` u root-u workspace-a (`judge-guard-core/`) — Antigravity IDE pretražuje od CWD naviše
- **Rules putanja:** `.agents/rules/verification.md` — `trigger: always_on`, limit 24KB
- **Hook skripte:** `scripts/` direktorijum u workspace root-u
- **Test runner:** `pytest` za Python hook skripte — nema mock-ova, samo stvarna validacija logike
- **MCP verifikacija:** Koristiti `call_mcp_tool` da zaista pozovemo oba servera i dokažemo da rade

## Task List

### Phase 1: Verifikacija MCP Servera (Funkcionalni Dokaz)
- [ ] Task 1: Verifikuj `personalized-service-health` MCP — pravi API poziv
- [ ] Task 2: Verifikuj `sequential-thinking` MCP — pravi tool poziv

### Checkpoint: Phase 1
- [ ] Oba MCP servera odgovaraju sa stvarnim podacima (ne mock)
- [ ] Tool schemas validni

### Phase 2: Hooks i Pravila
- [ ] Task 3: Kreiraj `.agents/rules/verification.md` sa `trigger: always_on`
- [ ] Task 4: Kreiraj `scripts/verify_command_safety.py` (hook skripta)
- [ ] Task 5: Kreiraj `scripts/log_audit.py` (post-tool audit logger)
- [ ] Task 6: Kreiraj `.agents/hooks.json` sa PreToolUse + PostToolUse

### Checkpoint: Phase 2
- [ ] `yamllint` ili `python3 -c "import frontmatter"` validira rules frontmatter
- [ ] Hook skripte izvršive i lintovane

### Phase 3: Testovi (Stvarni, Ne Mock)
- [ ] Task 7: Kreiraj `tests/test_hooks.py` — testovi za `verify_command_safety.py`
- [ ] Task 8: Kreiraj `tests/test_rules_frontmatter.py` — validacija YAML frontmatter pravila
- [ ] Task 9: Pokreni `pytest tests/test_hooks.py tests/test_rules_frontmatter.py` — Exit Code 0

### Checkpoint: Phase 3
- [ ] `pytest` prolazi sa 0 grešaka, 0 mock-ova
- [ ] `git diff` prikazuje sve kreirane datoteke
- [ ] WORK_LOG.md ažuriran sa `✅ Completed`

### Phase 4: Integracija i Finalni Dokaz
- [ ] Task 10: Upiši `✅ Completed` u WORK_LOG.md sa sve dokazima

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| `personalized-service-health` zahteva GCP project | High | Koristiti `formidable-gate-497822-r9` iz postojeće config |
| Hook ne blokira ako Antigravity ne učita `.agents/` | High | Verifikovati učitavanje ručnim testom + check docs |
| `sequential-thinking` zahteva `npx` i internet | Medium | Proveriti `npx --version` pre poziva |
| Frontmatter parse greška blokira pravilo | Medium | Validirati YAML sintaksu pre commit-a |

## Open Questions

- Da li Antigravity IDE čita `.agents/hooks.json` iz `judge-guard-core/` ili iz `~/.gemini/config/`?
- Da li hook payload format za `run_command` koristi `CommandLine` ili `command` ključ?
