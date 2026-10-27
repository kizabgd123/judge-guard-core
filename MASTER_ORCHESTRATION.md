# ⚖️ MASTER ORCHESTRATION: The Immutable Laws of Antigravity & JudgeGuard

**Authority:** Autonomous AI Agent Governance & Safety Constitution  
**Target Environment:** Antigravity IDE / Linux OS  
**Enforcement Status:** MANDATORY (Violation triggers HALT)

---

## Law 1: Zero-Simulation & Zero-Mock Policy (Absolute)
1. **No Production Mocks:** Mocking production security gates, authentication tokens, API responses, or system commands is strictly prohibited.
2. **No Fake Verifications:** Commands such as `deploy_to_prod` or `monitor_health` must NEVER be simulated with dummy success bypasses.
3. **Authentic Fallbacks Only:** If a cloud service (e.g. Gemini API, Notion API, Hugging Face) is offline or missing credentials, the system MUST use authentic, deterministic local evaluation or queue requests in a genuine offline queue with explicit logging. It must NEVER fabricate fake LLM responses or forged JWT tokens.
4. **Immediate Replacement:** Any mock, fake return value, dummy token, or simulated command discovered in the codebase must be removed and replaced with authentic verification or fail-fast diagnostics.

---

## Law 2: Mandatory JudgeGuard Pre-Action Verification Gate
1. **Execution Gating:** Before executing any critical operation (file writes, database schema migrations, code generation, dependency changes, deployments, or git commits), the action MUST pass through `judge_guard.py`.
2. **Layered Verification Pipeline:**
   - **Layer 00 (Security Hard Rules):** Blocks dangerous system operations (`sudo`, `rm -rf /`, root modifications).
   - **Layer 0 (Traceability & Work Log):** Enforces an active, non-stale `🟡 Starting <ACTION>` entry in `WORK_LOG.md` logged within the last 120 seconds.
   - **Layer 1 (Tool & Phase Discipline):** Ensures proper tool usage per phase (e.g., research phases must use browser/search rather than blind shell execution).
   - **Layer 2 (Visibility & Thought Streaming):** Emits live judgment states to the local bridge / PWA dashboard.
   - **Layer 3 (Project Essence & Semantic Drift):** Verifies that the proposed action aligns with the Golden Snapshot and contains <20% semantic drift.

---

## Law 3: Work Log Traceability & State Lifecycle
Every critical operation must strictly adhere to the following sequence in `WORK_LOG.md`:
1. `echo "🟡 Starting [ACTION]" >> WORK_LOG.md`
2. Run `python3 judge_guard.py "Start [ACTION]"`
3. If EXIT 0 (PASSED): execute the action.
4. If EXIT 1 (BLOCKED): STOP execution immediately, diagnose, fix, and re-verify.
5. Upon completion: `echo "✅ Completed [ACTION]" >> WORK_LOG.md`
6. Post-verification: `python3 judge_guard.py "Verify [ACTION] Complete"`
7. Checkpoint: `git add . && git commit -m "checkpoint: [ACTION]"`

---

## Law 4: Code Cleanliness, Quality & Test Discipline
1. **Compile & Test Gate:** No code may be marked completed or pushed without passing all unit/integration tests (`pytest`) and build gates (`npm run build`).
2. **Fail Fast:** Broken dependencies, invalid syntax (e.g. malformed shebangs), or obsolete paths (e.g. `/home/kizabgd/...`) must be resolved immediately upon discovery.
3. **Clean Git Hygiene:** The `main` branch represents verified, authentic, clean code. All changes must be verified against JudgeGuard before pushing to remote.

---

## Law 5: Anti-Circumvention, Anti-Echo & Cryptographic Execution Ticket Law
1. **Zero Evasion & Zero Tautology:** Submitting constitutional phrases, Golden Snapshot text, or abstract boilerplate to `judge_guard.py` instead of the concrete operational command and target is strictly prohibited and classified as an Adversarial Attack.
2. **Work Log Parity Enforcement:** The action submitted to `judge_guard.py` must match the active `🟡 Starting <ACTION>` entry in `WORK_LOG.md`. Falsification or disparity results in an immediate `Parity Violation Block`.
3. **Mandatory Execution Ticket Consumption:** No deployment script, external publisher (LinkedIn, Medium, Instagram), destructive command, or MCP tool may execute without presenting and atomically burning a valid, unexpired (TTL <= 60s), single-use HMAC-SHA256 Execution Ticket issued by JudgeGuard. Direct script execution without a ticket fails fast with Exit Code 43.
4. **Immediate Turn Halt on Block:** When `judge_guard.py` returns `BLOCKED (EXIT 1)`, the agent must IMMEDIATELY HALT. Automated retry loops or lexical substitutions designed to circumvent the block are prohibited. The agent must present the block diagnostics to the user and await explicit human instructions.
