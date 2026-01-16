# 🧪 Phase 3: Validation Plan

## 🎯 Goal

Testirati i validirati predložene šablone (Drift Score, Self-Healing, Browser CoT) u kontrolisanom okruženju kako bi se dokazala njihova efikasnost pre finalne implementacije u `judge_guard.py`.

---

## 🏗️ Test Scenarios

### 1. Drift Score Validation

- **Input:** Akcija koja je 50% usklađena sa `PROJECT_ESSENCE` (npr. modifikacija koda koja nije u planu ali nije ni destruktivna).
- **Metric:** Embedding similarity check (ili Gemini reasoning score).
- **Success Criteria:** Drift score koji logično raste sa stepenom devijacije.

### 2. Self-Healing Actor-Judge Loop

- **Input:** Akcija koja namerno krši pravila (npr. `run_command` tokom research faze).
- **Loop:**
  1. Actor predlaže.
  2. JudgeGuard Layer 3 odbija i vraća "Guidance" (npr. "Use search_web instead").
  3. Actor prima feedback i generiše novu (ispravnu) akciju.
- **Success Criteria:** Automatska korekcija bez ljudske intervencije (EXIT 1 -> EXIT 0).

### 3. Browser CoT Verification

- **Input:** Playwright/Puppeteer akcija (simulacija).
- **Test:** Uporediti DOM fragment pre i posle "klika" na element koji je pokriven drugim elementom (overlap).
- **Success Criteria:** Detekcija "Truth Mismatch" (Hipoteza: success toast, Reality: same DOM + error).

---

## 🛠️ Testing Tools

- Python scripts for simulation.
- Gemini API (za semantic check).
- `judge_guard.py` (kao test-bed).

---

## 📅 Timeline

- [ ] Setup simulation environment (Scripts)
- [ ] Run Drift & Self-Healing tests
- [ ] Document results in `test_results.md`
