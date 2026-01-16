# 🕵️ Phase 1 Discovery Report: Agent Taming Patterns

## 📂 Overview

Ovaj izveštaj sumira tehničke nalaze o kontrolnim obrascima, verifikaciji i sigurnosti agenata na dan 16. januar 2026.

---

## 🏗️ Arhitektonski Obrasci (Execution Patterns)

### 1. Supervisor-Worker Pattern (Nadzorni Model)

Umesto jednog agenta koji radi sve, sistem se deli na:

- **Orchestrator:** Upravlja stanjem, delegira taskove.
- **Workers:** Specijalizovani agenti sa ograničenim alatima (npr. "Search Worker", "Code Worker").
- **Validator:** Čvor koji proverava output pre nego što Supervisor nastavi dalje.

### 2. Multi-Layer Verification (CoVe 2026)

Struktura "Lanca Verifikacije" (Chain of Verification):

1. **Draft:** Generisanje bazičnog odgovora.
2. **Analysis:** Izdvajanje specifičnih tvrdnji koje zahtevaju dokaz.
3. **Execution:** Nezavisna pretraga dokaza za svaku tvrdnju.
4. **Logic Check:** Poređenje dokaza sa inicijalnim draftom (Cross-checking).

---

## 🛡️ Sigurnost i "Agentic Drift"

### Detekcija Drifta (LangGraph Implementation)

Agentic Drift se detektuje merenjem **semantike sličnosti** (cosine similarity) između originalnog zadatka (Objective) i trenutnog plana agenta.

**Primer Self-Healing Logike:**

```python
def healing_node(state: AgentState):
    original_objective = state["task"]
    current_thought = state["thoughts"][-1]

    # Ako drift pređe 0.3, resetuj context i vrati fokus na originalni task
    if state["drift_score"] > 0.3:
        return {
            "thoughts": state["thoughts"] + ["[HEAL] Detected semantic drift. Resetting focus to original goal."],
            "current_step": 0
        }
```

---

## 📜 Recursive Constitutional AI (Recursive CAI)

Jedno od najjačih otkrića je **JudgeFlow** koncept:

- **Model A (Actor):** Predlaže akciju.
- **Model B (Judge):** Pregleda "Thinking Trace" Modela A i proverava ga u odnosu na `PROJECT_ESSENCE`.
- **Feedback Loop:** Ako Judge odbije (EXIT 1), Actor mora da revidira plan dok ne dobije EXIT 0.

---

## 🛠️ Framework Audit

| Alat                | Use Case                                          | Rating     |
| :------------------ | :------------------------------------------------ | :--------- |
| **LangGraph**       | Kompleksni stateful workflow                      | ⭐️⭐️⭐️⭐️⭐️ |
| **Nemo Guardrails** | Filtriranje input/output u realnom vremenu        | ⭐️⭐️⭐️⭐️   |
| **Guardrails AI**   | Validacija struktuiranih podataka (JSON/Pydantic) | ⭐️⭐️⭐️⭐️   |

---

## 🚀 Preporuke za JudgeGuard

1. Implementirati **Drift Score** u Layer 3.
2. Uvesti **Self-Healing** petlju koja se aktivira naEXIT 1.
3. Razbiti Judge logic na dva dela: **Syntactic Check** (Pravila) i **Semantic Check** (Suština).

---

> **Status:** Phase 1 Discovery Complete.
