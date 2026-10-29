# 🔭 DISCOVERY FILE: Discovered Spaced Em-Dash Invariant in Claude Opus

**Session ID:** `session_test_01`
**Author:** Engineer Handoff (engineer)
**Competition:** `test_comp_handoff`
**Duration:** 60.0 minutes
**Metric Delta:** +0.0530
**Date:** 2026-10-29T01:37:19.072687+00:00

---

### 💡 What Worked
Spaced em-dash guard achieves 100% precision on Opus and GLM.

### 🛑 What Failed (Dead Ends to Avoid)
Linear blending without Sinkhorn balancing causes probability skew.

### 🔍 Invariants Discovered
- `spaced_em_dash`
- `curly_quote_zero`

### 📦 Artifacts & Code Generated
- `kernel_sub16.py`

### 🎯 Recommendations for the Next Agent
Enforce bipartite Hungarian matching on top of em-dash filtering.
