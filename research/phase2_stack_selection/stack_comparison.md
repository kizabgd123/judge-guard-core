# 📊 Phase 2: Tech Stack Selection & Analysis

> **Goal:** Identify the most "Agent-Friendly" mobile stack for 2026.
> **Method:** Google AI Search Comparison (Verified)

---

## 🏆 Comparative Matrix

| Feature                 | **Flutter**                             | **React Native**                   | **PWA (Progressive Web App)**                 | **Python (Kivy)**          |
| :---------------------- | :-------------------------------------- | :--------------------------------- | :-------------------------------------------- | :------------------------- |
| **Agent "Vibe Coding"** | ⭐⭐⭐⭐ (High quality Dart generation) | ⭐⭐⭐⭐ (Great v0/Cursor support) | ⭐⭐⭐⭐⭐ **(Best)** (Native web generation) | ⭐⭐ (Low, verbose syntax) |
| **Antigravity Fit**     | 🟠 Needs Bridge (Dart <-> Py)           | 🟠 Needs Bridge (JS <-> Py)        | 🟢 **Seamless** (REST/WebSocket)              | 🟢 Native Python           |
| **Performance**         | 🟢 **Native (120fps)**                  | 🟢 Very Good                       | 🟡 Good (No GPU heavy access)                 | 🔴 Slower Runtime          |
| **Production Ready**    | ✅ Enterprise Standard                  | ✅ Enterprise Standard             | ✅ Store-less Distribution                    | ⚠️ Niche / Specialized     |

---

## 🧠 Key Findings

1. **PWA is the "Vibe Coding" Champion:**
   - For rapid, agent-led development, PWAs offer the lowest friction. Agents excel at writing HTML/CSS/JS.
   - No need for complex build pipelines (Xcode/Android Studio) during the prototyping phase.
   - **Risk:** Limited access to deep hardware features (though WebBluetooth/WebUSB exist).

2. **Flutter is the "Power User" Choice:**
   - If the app requires heavy on-device AI (e.g., local LLM inference), Flutter's robust engine and typed nature (Dart) provide better stability.

3. **Python (Kivy) is a Trap:**
   - Despite being Python-native, the ecosystem limits production quality. It "feels" like a prototype tool.

---

## 🎯 Recommendation

**Primary Strategy: PWA First**

- **Why:** Fits perfectly with Antigravity's web-based agent nature. Agents can "see" and "edit" the web app instantly without compilation steps.
- **Fallback:** React Native (Expo) if native store presence is strictly required later.

---

## 🖼️ Verification

![Comparison Evidence](/home/kizabgd/Desktop/33333333333333333333/research/phase2_stack_selection/comparison_evidence.png)
_Figure 1: AI Search Comparison showing PWA's dominance in "Vibe Coding"._
