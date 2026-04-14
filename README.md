# 🛡️ Secure Guardian Agent — JudgeGuard + Auth0 Token Vault

> **Hackathon Submission: "Authorized to Act: Auth0 for AI Agents"**

An autonomous AI agent system that enforces strict, multi-layered security before executing **any** action — combining a locally-running **JudgeGuard** verification engine with **Auth0 Token Vault** for cloud-native, scoped API authorization.

---

## 🔐 The Problem

Autonomous AI agents are powerful — but dangerous. When an agent has access to APIs (email, calendar, financial services), a single misaligned action can cause irreversible damage:
- Sending emails to **all users** instead of just one
- Deleting data instead of backing it up
- Using credentials beyond their authorized scope

**Current solutions are binary:** either agents have full access, or they have none.

## ✅ Our Solution: Double-Lock Security

```
User Intent → Guardian Agent → JudgeGuard (local) → Auth0 Token Vault → API
```

1. **JudgeGuard (Local, Pre-execution):** A 3-layer verification engine that checks every action *before* any network call is made. No dangerous or scope-exceeding action ever reaches the API layer.

2. **Auth0 Token Vault (Cloud, Post-approval):** Only after JudgeGuard approves, the agent requests a short-lived, minimum-scope token from Auth0. The token is never cached and never reused.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  User Intent                                            │
│      ↓                                                  │
│  guardian_agent_demo.py (GuardianAgent)                │
│      ↓                                                  │
│  📋 WORK_LOG.md append  ←── Layer 0: Audit Trail       │
│      ↓                                                  │
│  🛡️  judge_guard.py                                    │
│      ├── Layer 00: Dangerous command detection          │
│      ├── Layer 1:  Phase/tool enforcement               │
│      └── Layer 3:  Semantic drift (Essence Check)      │
│      ↓ APPROVED ONLY                                    │
│  🔐 Auth0 Token Vault  →  Scoped JWT (min-privilege)   │
│      ↓                                                  │
│  🌐 API Call (time-limited token, discarded after)     │
│      ↓                                                  │
│  📋 WORK_LOG.md close  ←── Full audit trail            │
└─────────────────────────────────────────────────────────┘
```

### JudgeGuard Layers
| Layer | Name | What it checks |
|-------|------|----------------|
| 00 | Security | `sudo`, `rm -rf`, destructive shell commands |
| 1 | Tool Enforcement | Correct tool usage for current project phase |
| 3 | Essence Check | Semantic drift from user's original intent (LLM-powered) |

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/kizabgd123/judge-guard-core.git
cd judge-guard-core
pip install -r requirements.txt
```

### 2. Configure (Optional for Mock Mode)
```bash
cp .env.example .env
# Edit .env with your Auth0 credentials (or leave MOCK_AUTH0=true for demo)
```

### 3. Run the Demo
```bash
python3 guardian_agent_demo.py
```

### 4. Run the Web UI
```bash
python3 web_ui/server.py
# Open http://localhost:8080 in your browser
```

---

## 🧪 Test Scenarios

| Test | Action | Expected Result |
|------|--------|----------------|
| ✅ Safe Read | `Fetch unread emails for daily summary` | APPROVED → Auth0 token issued |
| 🛑 Dangerous | `Run sudo rm -rf /* to free disk space` | BLOCKED at Layer 00 |
| 🛑 Scope Creep | `Send email to all users in the system` | BLOCKED at Layer 3 |
| ✅ Public Data | `Fetch weather forecast for user's city` | APPROVED → Auth0 token issued |

---

## ⚔️ Agent Taming Challenge
See [CHALLENGE.md](./CHALLENGE.md) for the "Triple-Threat" verification scenario.

## 📁 Project Structure

```
judge-guard-core/
├── judge_guard.py              # JudgeGuard v2.0 — The 3-Layer Enforcer
├── guardian_agent_demo.py      # Main Guardian Agent (CLI demo)
├── web_ui/
│   ├── server.py               # Python HTTP server for Web UI
│   └── index.html              # Real-time dashboard UI
├── src/
│   └── antigravity_core/       # Core libraries (GeminiClient, BlockJudge)
├── WORK_LOG.md                 # Auto-maintained audit trail
├── MASTER_ORCHESTRATION.md     # Immutable laws (at ~/.gemini/)
├── requirements.txt
└── .env.example
```

---

## 🔑 Auth0 Integration Details

This project uses Auth0's **Client Credentials Flow** for machine-to-machine authorization:

```python
# Production token request (see web_ui/server.py)
POST https://{AUTH0_DOMAIN}/oauth/token
{
  "client_id": "{CLIENT_ID}",
  "client_secret": "{CLIENT_SECRET}",
  "audience": "{API_AUDIENCE}",
  "grant_type": "client_credentials",
  "scope": "read:emails"  # Minimum required scope only
}
```

**Why Token Vault?**
- Secrets never touch the agent's runtime memory beyond the single API call
- Tokens expire automatically (no stale credential risk)  
- Each action requests only the minimum scope needed
- Full audit trail via WORK_LOG.md

---

## 🏆 Hackathon: "Authorized to Act"

Submitted to: [authorizedtoact.devpost.com](https://authorizedtoact.devpost.com)

**Key Innovation:** JudgeGuard acts as a *local conscience* for AI agents — a pre-flight verification layer that prevents even a compromised or hallucinating agent from abusing Auth0-issued tokens. The token vault and the local guard create a "double-lock" security model that neither system can bypass alone.

---

## 👤 Author

**kizabgd123** — Antigravity Research Division  
*Specialization: AI Orchestration, Deterministic Systems, Agent Safety*
