# 🎯 Agent Taming: Advanced Control & Verification Guide

> **Project Authority:** Antigravity Research Division
> **Focus:** Reliable, deterministic, and safe AI agent behavior.

## 📂 Overview

Ovaj vodič predstavlja vrhunac istraživanja o kontroli agenata, fokusirajući se na eliminaciju "agentic drift-a" i obezbeđivanje determinističkih interakcija u browser okruženjima.

---

## 🏛️ The Verification Architecture (JudgeGuard v2.1)

JudgeGuard v2.1 koristi troslojni model verifikacije koji osigurava da agenti nikada ne izlaze iz okvira zadate "Esencije Projekta".

### Layer 1: Tool & Context Enforcement

- **Svrha:** Blokiranje opasnih komandi i osiguranje da se koristi ispravan alat za fazu istraživanja.
- **Rule:** U fazama 0 i 1 (Research), `run_command` je zabranjen; browser agent je obavezan.

### Layer 2: Live Thought Streaming

- **Svrha:** Transparentnost. Svaka odluka sudije se strimuje na mobilni most pre izvršenja.
- **Implementacija:** `bridge.push_verdict()` pre svakog PASSED/FAILED signala.

### Layer 3: Semantic Drift Scoring 🚀

- **Svrha:** Merenje semantičkog odstupanja svake akcije od "Zlatnog Snimka" (Golden Snapshot).
- **Metric:** `drift_score` (0.0 - 1.0). Limit: **0.4**.
- **Self-Healing:** Ako akcija padne na drift testu, sudija šalje feedback, a Actor-Judge loop omogućava automatsku korekciju.

---

## 🌐 Browser "Chain of Truth" (CoT) Loop

Za pouzdanu automatizaciju browsera, agent mora pratiti 5-stepeni ciklus:

1. **Observe & Anchor:** Pre klika, pronađi stabilne elemente (ne samo selektore).
2. **Predict:** Šta se očekuje nakon akcije? (npr. URL promena, novi modal).
3. **Act:** Izvrši interaction.
4. **Verify State:** Da li je predikcija tačna? Ako ne -> Error State.
5. **Visual Confirmation:** Koristi screenshot za finalnu validaciju (Multimodal CoT).

---

## 🛠️ Implementation Blueprints

### 1. Drift Detector Snippet

```python
def check_drift(action, essence):
    prompt = f"Does '{action}' drift from '{essence}'? Reply with score."
    # ... logic from drift_prototype.py
```

### 2. Self-Healing Loop

```python
while attempt < max:
    result = actor.act(context)
    if judge.verify(result):
       return result
    context['feedback'] = judge.get_reason()
```

---

## 🏁 Conclusion

Agent Taming nije restrikcija, već **osnaživanje**. Davanjem jasnih granica agentima, omogućavamo im da operišu punom snagom u sigurnom i predvidljivom okviru.

> **Final Verdict:** Verified & Documented.
