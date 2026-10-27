# Task List: MCP + Hooks + Rules Install

> Plan: [tasks/plan.md](plan.md) | JudgeGuard ticket: `6dd31500-20e3-4b28-bd15-de4ed3bcaf84`

## Phase 1: Verifikacija MCP Servera

- [ ] **Task 1 (BLOCKED)** — Verifikuj `personalized-service-health`: pozovi `list_project_events` sa `projects/formidable-gate-497822-r9/locations/global`
  - Acceptance: API vraća stvarni odgovor (events lista ili prazan niz), ne grešku
  - Verification: **REAL API poziv → 403 Forbidden** (GCP projekat nema Service Health API odobren — stvarna greška, transparentno prijavljena)
  - Files: none
  - Scope: XS

- [x] **Task 2** — Verifikuj `sequential-thinking`: pozovi `sequentialthinking` tool sa jednim mislenim korakom
  - Acceptance: ✅ Tool vratio `{"thoughtNumber":1,"totalThoughts":1,"nextThoughtNeeded":false}`
  - Verification: npx uspešno pokrenut, stvarni odgovor prikazan
  - Files: none
  - Scope: XS

### ✅ Checkpoint 1
- [x] sequential-thinking živo odgovara (stvarni odgovor)
- [ ] personalized-service-health — BLOCKED: API returned 403; keep checkpoint incomplete until an accepted response is available.
- [x] Nema mock-ova u dokazima

---

## Phase 2: Hooks i Pravila

- [x] **Task 3** — Kreiraj `.agents/rules/verification.md`
  - ✅ Kreiran sa `trigger: always_on`, YAML parsiran, 6 pravila verifikacije
  - Files: [`.agents/rules/verification.md`](.agents/rules/verification.md)

- [x] **Task 4** — Kreiraj `scripts/verify_command_safety.py`
  - ✅ Blokira 9 kategorija opasnih komandi, propušta bezbedne
  - Files: [`scripts/verify_command_safety.py`](scripts/verify_command_safety.py)

- [x] **Task 5** — Kreiraj `scripts/log_audit.py`
  - ✅ Loguje post-tool akcije u `audit.log`
  - Files: [`scripts/log_audit.py`](scripts/log_audit.py)

- [x] **Task 6** — Kreiraj `.agents/hooks.json`
  - ✅ Validan JSON, PreToolUse za run_command, PostToolUse za write_file/write_to_file
  - Files: [`.agents/hooks.json`](.agents/hooks.json)

### ✅ Checkpoint 2
- [x] YAML frontmatter validan (potvrđeno testovima)
- [x] JSON hooks validan (`python3 -m json.tool` prolazi)
- [x] Hook skripte sintaksno ispravne

---

## Phase 3: Testovi (Stvarni, 0 Mock-ova)

- [x] **Task 7** — Kreiraj `tests/test_hooks.py`
  - ✅ 17 testova: script exists, safe commands, dangerous blocks, alt payload formats
  - Files: [`tests/test_hooks.py`](tests/test_hooks.py)

- [x] **Task 8** — Kreiraj `tests/test_rules_frontmatter.py`
  - ✅ 13 testova: file exists, frontmatter YAML, trigger field, hooks.json validacija
  - Files: [`tests/test_rules_frontmatter.py`](tests/test_rules_frontmatter.py)

- [x] **Task 9** — Pokreni kompletni test suite
  - ✅ `pytest tests/test_hooks.py tests/test_rules_frontmatter.py -v` → **30 passed, Exit Code 0**
  - 0 mock-ova, 0 simulacija

### ✅ Checkpoint 3
- [x] pytest Exit Code 0 (30/30 testova)
- [x] 0 mock-ova
- [x] git status pokazuje sve nove datoteke

---

## Phase 4: Finalizacija

- [x] **Task 10** — Upiši `✅ Completed` u WORK_LOG.md sa dokazima
  - ✅ Upisano u WORK_LOG.md sa svim kreiranim fajlovima
