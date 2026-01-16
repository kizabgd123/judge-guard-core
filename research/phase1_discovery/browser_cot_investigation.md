# 🔬 Renewed Investigation: Advanced Browser CoT Patterns

## 📂 Overview

Ovaj izveštaj detaljno opisuje "Chain of Truth" (CoT) operativni model za browser agente, fokusiran na eliminaciju halucinacija i determinističko izvršavanje u dinamičkim UI okruženjima.

---

## 🏗️ The Chain of Truth (CoT) Loop

Implementacioni ciklus se sastoji od 5 faza koje garantuju sinhronizaciju između internog stanja agenta i eksterne realnosti browsera.

### 1. 👁️ Observation (State Anchoring)

Agent mora identifikovati **Anchors** (sidra) - elemente koji se ne menjaju ili jedinstveno identifikuju trenutnu stranicu.

- **Tehnika:** XPath/CSS selektori nisu dovoljni. Koristi se **Semantic Anchoring** (npr. "Presence of 'Checkout' header + URL path /cart").
- **Audit:** Svaki korak mora početi sa `[OBSERVATION]` logom.

### 2. 🧠 Reasoning (Logic Bridge)

Povezivanje cilja sa opserviranim stanjem.

- **Pitanje:** "Gde sam i šta je moj sledeći minimalni korak?"

### 3. 🧪 Hypothesis (Expected Truth)

Pre svake akcije, agent **mora** definisati šta očekuje da vidi _nakon_ akcije.

- **Primer:** "Nakon klika na 'Add to Cart', očekujem da se 'Subtotal' poveća ili da se pojavi 'Success' toast."

### 4. ⚡ Action (Execution)

Minimalna tehnička interakcija (click, type, navigate).

### 5. ✅ Verification (Ground Truth Sync)

Poređenje Hipoteze (Faza 3) sa novom Opservacijom. Ako `Verification != Hypothesis`, aktivira se **Self-Healing**.

---

## 🛡️ Agentic Drift Detection

Drift se meri kao **Semantic Divergence** između:

1. `USER_GOAL` (Suština zadatka)
2. `CURRENT_STATE` (Trenutni DOM + Akcija)

**Formula za Self-Healing:**

- **Trigger:** URL mismatch ili missing Anchor.
- **Action:** Resetuj DOM snapshot, obriši privremeni context, i ponovi Fazu 1 (Observation).

---

## 🚀 Preporuke za JudgeGuard (Layer 3)

1. **State Snapshotting:** Pre i posle svake browser akcije, JudgeGuard treba da uporedi DOM fragment.
2. **Context Memento:** Uvesti read-only manifest pravila koji se re-injectuje u svaki browser prompt ("Ground Truth Manifest").
3. **Visual Guardrails:** Integracija sa vision modelima za potvrdu da "dugme zaista postoji" uprkos tome što je u DOM-u skriveno ili blokirano.

---

> **Status:** Renewed Investigation Complete.
> **Next Step:** Integrate findings into JudgeGuard implementation plan.
