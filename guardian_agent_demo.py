#!/usr/bin/env python3
"""
Guardian Agent Demo v1.0
Auth0 Token Vault + JudgeGuard Integration POC

Usage:
    python3 guardian_agent_demo.py

This demo shows how an AI agent:
1. Requests a token from Auth0 Token Vault (mocked for demo)
2. Passes every action through JudgeGuard's 3-layer verification
3. Only uses the token if JudgeGuard APPROVES the action
4. Blocks destructive or scope-creeping actions automatically

Architecture:
    User Intent -> Guardian Agent -> JudgeGuard (local) -> Auth0 Token Vault (cloud) -> API
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
WORK_LOG_PATH = os.getenv("WORK_LOG_PATH", "./WORK_LOG.md")
MOCK_AUTH0 = os.getenv("MOCK_AUTH0", "true").lower() == "true"
MOCK_GEMINI_JUDGE = os.getenv("MOCK_GEMINI_JUDGE", "true").lower() == "true"
JUDGE_GUARD_SCRIPT = os.path.join(os.path.dirname(__file__), "judge_guard.py")


# ═══════════════════════════════════════════════════════
# BLOCK 1: WORK LOG MANAGER
# Required by JudgeGuard Layer 0 (Work Log Enforcement)
# ═══════════════════════════════════════════════════════

class WorkLogManager:
    """Manages the WORK_LOG.md file required by JudgeGuard Layer 0."""
    
    def __init__(self, log_path: str = WORK_LOG_PATH):
        self.log_path = log_path

    def log(self, emoji: str, message: str):
        timestamp = datetime.now().isoformat()
        entry = f"{emoji} {message} at {timestamp}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"  📋 WorkLog: {entry.strip()}")

    def start_action(self, action: str):
        """Required format for JudgeGuard Layer 0 to pass."""
        self.log("🟡", f"Starting {action}")

    def complete_action(self, action: str):
        self.log("✅", f"Completed {action}")

    def block_action(self, action: str, reason: str):
        self.log("🔴", f"BLOCKED {action} - Reason: {reason}")


# ═══════════════════════════════════════════════════════
# BLOCK 2: AUTH0 TOKEN VAULT (Mock / Production)
# In production: uses Auth0 Management API + Token Vault
# ═══════════════════════════════════════════════════════

class Auth0TokenVault:
    """
    Simulates Auth0 Token Vault behavior.
    
    In production this would:
    1. Authenticate with Auth0 using Client Credentials flow
    2. Request a scoped token for the specific API
    3. Return a short-lived JWT for that API only
    4. NEVER expose the token beyond the authorized request
    
    Production endpoint: POST https://{AUTH0_DOMAIN}/oauth/token
    """
    
    def __init__(self):
        self.domain = os.getenv("AUTH0_DOMAIN", "demo.auth0.com")
        self.client_id = os.getenv("AUTH0_CLIENT_ID", "demo_client_id")
        self.audience = os.getenv("AUTH0_AUDIENCE", "https://demo-api")
        self._token_cache = {}
    
    def get_token(self, scope: str) -> Optional[str]:
        """
        Request a scoped token from Auth0 Token Vault.
        
        Args:
            scope: The specific permission scope needed (e.g., 'read:emails')
            
        Returns:
            A JWT token string, or None if auth fails
        """
        if MOCK_AUTH0:
            # Mock: simulate Token Vault response
            print(f"\n  🔐 [Auth0 Token Vault] Requesting token for scope: '{scope}'")
            print(f"     Domain: {self.domain}")
            print(f"     Client: {self.client_id[:8]}...")
            time.sleep(0.3)  # simulate network latency
            
            # Generate mock token per scope
            mock_token = f"mock_jwt_{scope.replace(':', '_')}_{int(time.time())}"
            print(f"  ✅ [Auth0 Token Vault] Token issued: {mock_token[:30]}...")
            return mock_token
        else:
            # Production: real Auth0 call
            try:
                import requests
                response = requests.post(
                    f"https://{self.domain}/oauth/token",
                    json={
                        "client_id": self.client_id,
                        "client_secret": os.getenv("AUTH0_CLIENT_SECRET"),
                        "audience": self.audience,
                        "grant_type": "client_credentials",
                        "scope": scope
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json().get("access_token")
                else:
                    print(f"  ❌ Auth0 error: {response.status_code}")
                    return None
            except Exception as e:
                print(f"  ❌ Auth0 connection error: {e}")
                return None
    
    def execute_api_call(self, token: str, api_endpoint: str, payload: dict) -> dict:
        """
        Execute an API call using the Auth0-issued token.
        Token is used only for this specific call and then discarded.
        """
        if MOCK_AUTH0:
            print(f"\n  🌐 [API Call] POST {api_endpoint}")
            print(f"     Authorization: Bearer {token[:20]}...")
            print(f"     Payload: {payload}")
            time.sleep(0.2)  # simulate API response
            return {"status": "success", "message": f"Action completed via {api_endpoint}"}
        else:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(api_endpoint, json=payload, headers=headers, timeout=10)
            return response.json()


# ═══════════════════════════════════════════════════════
# BLOCK 3: JUDGEGUARD INTEGRATION
# Calls judge_guard.py as a subprocess (CLI enforcer)
# ═══════════════════════════════════════════════════════

class JudgeGuardClient:
    """
    Client for JudgeGuard v2.0 enforcement.
    
    Calls judge_guard.py as a subprocess to maintain isolation.
    Exit code 0 = APPROVED
    Exit code 1 = BLOCKED
    """
    
    def __init__(self, script_path: str = JUDGE_GUARD_SCRIPT):
        self.script_path = script_path
        self.work_log = WorkLogManager()
    
    def verify(self, action: str) -> bool:
        """
        Submit an action for JudgeGuard verification.
        
        Returns True if approved, False if blocked.
        """
        print(f"\n  🛡️  [JudgeGuard] Submitting for verification: '{action}'")
        
        if MOCK_GEMINI_JUDGE:
            # Mock mode: simulate JudgeGuard logic locally for demo
            return self._mock_judge(action)
        else:
            # Production: call real judge_guard.py
            return self._real_judge(action)
    
    def _mock_judge(self, action: str) -> bool:
        """Mock JudgeGuard that simulates the 3-layer verification."""
        action_lower = action.lower()
        
        print("     Running Layer 00: Security Check...")
        time.sleep(0.1)
        dangerous = ["sudo", "rm -rf", "delete all", "destroy", "wipe", "drop table", "purge all"]
        if any(d in action_lower for d in dangerous):
            print("     🛑 Layer 00 BLOCKED: Dangerous command detected!")
            return False
        print("     ✅ Layer 00: PASSED")
        
        print("     Running Layer 1: Tool Enforcement...")
        time.sleep(0.1)
        print("     ✅ Layer 1: PASSED (Correct phase/tool usage)")
        
        print("     Running Layer 3: Essence Check (Semantic Drift)...")
        time.sleep(0.2)
        
        # Essence check: destructive or scope-creeping actions
        scope_violations = [
            "send email to all", "mass delete", "access financial", 
            "bypass security", "ignore judge", "skip verification",
            "delete account", "remove all users"
        ]
        for violation in scope_violations:
            if violation in action_lower:
                print(f"     🛑 Layer 3 BLOCKED: Semantic drift detected — '{violation}'")
                return False
        
        print("     ✅ Layer 3: PASSED (Action aligns with Project Essence)")
        return True
    
    def _real_judge(self, action: str) -> bool:
        """Call the real judge_guard.py script."""
        try:
            result = subprocess.run(
                ["python3", self.script_path, action],
                capture_output=True,
                text=True,
                timeout=30
            )
            print(result.stdout)
            if result.stderr:
                print(f"     stderr: {result.stderr[:200]}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("     ⚠️  JudgeGuard timed out — blocking as precaution")
            return False
        except Exception as e:
            print(f"     ⚠️  JudgeGuard error: {e} — blocking as precaution")
            return False


# ═══════════════════════════════════════════════════════
# BLOCK 4: GUARDIAN AGENT — Main Orchestrator
# ═══════════════════════════════════════════════════════

class GuardianAgent:
    """
    The main AI Agent that orchestrates:
    1. User intent parsing
    2. JudgeGuard verification (local, before any API call)
    3. Auth0 Token Vault for secure, scoped API access
    
    Security Model:
    ┌──────────────────────────────────────────────────────┐
    │  User Intent                                         │
    │      ↓                                               │
    │  GuardianAgent.execute_tool()                        │
    │      ↓                                               │
    │  WorkLog.start_action()  ← Layer 0 requirement      │
    │      ↓                                               │
    │  JudgeGuard.verify()     ← 3-Layer check            │
    │      ↓ APPROVED                                      │
    │  Auth0TokenVault.get_token(scope)                    │
    │      ↓                                               │
    │  API Call with scoped token                          │
    │      ↓                                               │
    │  WorkLog.complete_action()                           │
    └──────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        self.vault = Auth0TokenVault()
        self.judge = JudgeGuardClient()
        self.work_log = WorkLogManager()
        print("🤖 GuardianAgent initialized.")
        print(f"   Mode: {'MOCK (Demo)' if MOCK_AUTH0 else 'PRODUCTION (Real Auth0)'}")
        print(f"   JudgeGuard: {'MOCK (Local Simulation)' if MOCK_GEMINI_JUDGE else 'REAL (Gemini-powered)'}")
    
    def execute_tool(self, tool_name: str, description: str, scope: str, api_endpoint: str, payload: dict) -> dict:
        """
        Execute a tool action through the full Guardian security pipeline.
        
        Args:
            tool_name: Name of the tool/action (e.g., 'ReadEmails')
            description: Human-readable description of the action (for JudgeGuard)
            scope: Required Auth0 scope (e.g., 'read:emails')
            api_endpoint: Target API endpoint
            payload: Request payload
            
        Returns:
            Result dict with 'approved', 'result', and 'reason' keys
        """
        print(f"\n{'═'*60}")
        print(f"⚙️  TOOL REQUEST: {tool_name}")
        print(f"   Description: {description}")
        print(f"   Required Scope: {scope}")
        print(f"{'═'*60}")
        
        # STEP 1: Log to WORK_LOG.md (required for JudgeGuard Layer 0)
        self.work_log.start_action(tool_name)
        
        # STEP 2: JudgeGuard Verification BEFORE any token request
        approved = self.judge.verify(description)
        
        if not approved:
            reason = f"JudgeGuard blocked: '{description}'"
            self.work_log.block_action(tool_name, reason)
            print(f"\n🛑 RESULT: ACTION BLOCKED by JudgeGuard")
            return {"approved": False, "result": None, "reason": reason}
        
        print(f"\n  ✅ JudgeGuard APPROVED action: '{tool_name}'")
        
        # STEP 3: Request scoped token from Auth0 Token Vault
        token = self.vault.get_token(scope)
        
        if not token:
            reason = "Auth0 Token Vault failed to issue token"
            self.work_log.block_action(tool_name, reason)
            return {"approved": False, "result": None, "reason": reason}
        
        # STEP 4: Execute the API call with the token
        result = self.vault.execute_api_call(token, api_endpoint, payload)
        
        # STEP 5: Log completion
        self.work_log.complete_action(tool_name)
        
        print(f"\n✅ RESULT: SUCCESS")
        print(f"   API Response: {result}")
        return {"approved": True, "result": result, "reason": "Approved and executed successfully"}


# ═══════════════════════════════════════════════════════
# MAIN DEMO — Test Scenarios
# ═══════════════════════════════════════════════════════

def run_demo():
    print("\n" + "█"*60)
    print("█   JudgeGuard + Auth0 Token Vault — POC Demo   █")
    print("█   Secure Guardian Agent v1.0                  █")
    print("█"*60)
    
    agent = GuardianAgent()
    
    # ─────────────────────────────────────────────────────
    # TEST 1: GOOD ACTION — Should PASS all layers ✅
    # ─────────────────────────────────────────────────────
    print("\n\n🧪 TEST 1: Safe Read Action (Expected: APPROVED)")
    result1 = agent.execute_tool(
        tool_name="ReadUnreadEmails",
        description="Fetch unread emails from inbox to summarize daily digest for user",
        scope="read:emails",
        api_endpoint="https://api.example.com/emails?filter=unread",
        payload={"limit": 10, "format": "summary"}
    )
    
    # ─────────────────────────────────────────────────────
    # TEST 2: DANGEROUS ACTION — Should be BLOCKED Layer 00 🛑
    # ─────────────────────────────────────────────────────
    print("\n\n🧪 TEST 2: Dangerous Shell Command (Expected: BLOCKED by Layer 00)")
    result2 = agent.execute_tool(
        tool_name="CleanupDisk",
        description="Run sudo rm -rf /* to free up disk space on the server",
        scope="admin:system",
        api_endpoint="https://api.example.com/system/cleanup",
        payload={"target": "/", "recursive": True}
    )
    
    # ─────────────────────────────────────────────────────
    # TEST 3: SCOPE CREEP — Should be BLOCKED by Layer 3 🛑
    # ─────────────────────────────────────────────────────
    print("\n\n🧪 TEST 3: Scope Creep — Unauthorized Mass Action (Expected: BLOCKED by Layer 3)")
    result3 = agent.execute_tool(
        tool_name="MassNotify",
        description="Send email to all users in the system about a new product update",
        scope="write:emails",
        api_endpoint="https://api.example.com/emails/send-bulk",
        payload={"to": "ALL_USERS", "template": "marketing_blast"}
    )
    
    # ─────────────────────────────────────────────────────
    # TEST 4: ANOTHER GOOD ACTION — Read public data ✅
    # ─────────────────────────────────────────────────────
    print("\n\n🧪 TEST 4: Fetch Weather Data (Expected: APPROVED)")
    result4 = agent.execute_tool(
        tool_name="GetWeatherForecast",
        description="Fetch weather forecast for user's location to plan their schedule",
        scope="read:weather",
        api_endpoint="https://api.openweathermap.org/data/2.5/forecast",
        payload={"city": "Belgrade", "units": "metric"}
    )
    
    # ─────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────
    print("\n\n" + "═"*60)
    print("📊 DEMO SUMMARY")
    print("═"*60)
    results = [
        ("ReadUnreadEmails", result1),
        ("CleanupDisk (dangerous)", result2),
        ("MassNotify (scope creep)", result3),
        ("GetWeatherForecast", result4),
    ]
    for name, r in results:
        icon = "✅ APPROVED" if r["approved"] else "🛑 BLOCKED"
        print(f"  {icon:<14} — {name}")
        if not r["approved"]:
            print(f"               Reason: {r['reason']}")
    
    print("\n✅ Demo complete. Check WORK_LOG.md for full audit trail.")
    print("═"*60)


if __name__ == "__main__":
    run_demo()
