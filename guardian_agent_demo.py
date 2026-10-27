#!/usr/bin/env python3
"""
Guardian Agent v2.0 - Auth0 Token Vault + JudgeGuard Real Integration
====================================================================
Usage:
    python3 guardian_agent_demo.py

Architecture:
    User Intent -> Guardian Agent -> JudgeGuard (real verification) -> Auth0 Token Vault -> API

Enforces the Zero-Mock Policy:
- Real JudgeGuard 3-layer verification for all actions.
- Real RFC 6749 OAuth2 Token Vault requests when credentials are configured.
- Zero fake JWT tokens or simulated success intercepts.
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from typing import Optional, Dict
from src.antigravity_core.env_utils import safe_load_dotenv

safe_load_dotenv()

# --- Configuration ---
WORK_LOG_PATH = os.getenv("WORK_LOG_PATH", "./WORK_LOG.md")
JUDGE_GUARD_SCRIPT = os.path.join(os.path.dirname(__file__), "judge_guard.py")


# ═══════════════════════════════════════════════════════
# BLOCK 1: WORK LOG MANAGER
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
# BLOCK 2: AUTH0 TOKEN VAULT (Real OAuth2 Client Credentials)
# ═══════════════════════════════════════════════════════

class Auth0TokenVault:
    """
    Authentic Auth0 Token Vault client.
    Issues short-lived scoped tokens via OAuth2 Client Credentials flow.
    Enforces Zero-Mock policy: does not forge fake tokens when credentials are missing.
    """
    
    def __init__(self):
        safe_load_dotenv()
        self.domain = os.getenv("AUTH0_DOMAIN", "").strip()
        self.client_id = os.getenv("AUTH0_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("AUTH0_CLIENT_SECRET", "").strip()
        self.audience = os.getenv("AUTH0_AUDIENCE", "").strip()
        self._token_cache = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.domain and self.client_id and self.client_secret and self.audience)
    
    def get_token(self, scope: str) -> Optional[str]:
        """
        Request a scoped token from Auth0 Token Vault.
        """
        if not self.is_configured:
            print(f"\n  ⚠️  [Auth0 Token Vault] Credentials not configured in .env (AUTH0_DOMAIN, CLIENT_ID, SECRET).")
            print("     Zero-Mock Policy: Refusing to generate synthetic JWT token.")
            return None

        try:
            import requests
            url = f"https://{self.domain}/oauth/token"
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": self.audience,
                "grant_type": "client_credentials",
                "scope": scope
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                print(f"  ✅ [Auth0 Token Vault] Authentic token issued for scope: '{scope}'")
                return token
            else:
                print(f"  🛑 Auth0 Token Request failed with HTTP {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            print(f"  🛑 Auth0 Connection error: {e}")
            return None
    
    def execute_api_call(self, token: str, api_endpoint: str, payload: dict) -> dict:
        """
        Execute an API call using the issued token.
        """
        import requests
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(api_endpoint, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()


# ═══════════════════════════════════════════════════════
# BLOCK 3: JUDGEGUARD INTEGRATION (Real Subprocess Verification)
# ═══════════════════════════════════════════════════════

class JudgeGuardClient:
    """
    Submits actions to the real JudgeGuard pipeline with zero simulation.
    """
    
    def __init__(self, script_path: str = JUDGE_GUARD_SCRIPT):
        self.script_path = script_path
        self.work_log = WorkLogManager()
    
    def verify(self, action: str) -> bool:
        print(f"\n  🛡️  [JudgeGuard] Submitting for real verification: '{action}'")
        try:
            result = subprocess.run(
                [sys.executable, self.script_path, action],
                capture_output=True,
                text=True,
                timeout=30
            )
            print(result.stdout.strip())
            if result.stderr:
                print(f"     stderr: {result.stderr.strip()[:200]}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("     ⚠️  JudgeGuard timed out — blocking as safety precaution.")
            return False
        except Exception as e:
            print(f"     ⚠️  JudgeGuard error: {e} — blocking as safety precaution.")
            return False


# ═══════════════════════════════════════════════════════
# BLOCK 4: GUARDIAN AGENT — Main Orchestrator
# ═══════════════════════════════════════════════════════

class GuardianAgent:
    """
    Main Guardian Orchestrator:
    1. Logs Intent to WORK_LOG.md
    2. Runs Real JudgeGuard Verification
    3. Requests Scoped Token from Auth0 Token Vault
    4. Executes API call only upon approval
    """
    
    def __init__(self):
        self.vault = Auth0TokenVault()
        self.judge = JudgeGuardClient()
        self.work_log = WorkLogManager()
        print("🤖 GuardianAgent v2.0 initialized (Authentic Zero-Mock Mode).")
    
    def execute_tool(self, tool_name: str, description: str, scope: str, api_endpoint: str, payload: dict) -> dict:
        print(f"\n{'═'*60}")
        print(f"⚙️  TOOL REQUEST: {tool_name}")
        print(f"   Description: {description}")
        print(f"   Required Scope: {scope}")
        print(f"{'═'*60}")
        
        # STEP 1: Log to WORK_LOG.md
        self.work_log.start_action(tool_name)
        
        # STEP 2: Real JudgeGuard Verification
        approved = self.judge.verify(description)
        
        if not approved:
            reason = f"JudgeGuard blocked: '{description}'"
            self.work_log.block_action(tool_name, reason)
            print(f"\n🛑 RESULT: ACTION BLOCKED by JudgeGuard")
            return {"approved": False, "result": None, "reason": reason}
        
        print(f"\n  ✅ JudgeGuard APPROVED action: '{tool_name}'")
        
        # STEP 3: Request token from Token Vault
        token = self.vault.get_token(scope)
        if not token:
            reason = "Auth0 Token Vault: Credentials unconfigured or token request rejected."
            self.work_log.block_action(tool_name, reason)
            return {"approved": False, "result": None, "reason": reason}
        
        # STEP 4: Execute API call
        try:
            result = self.vault.execute_api_call(token, api_endpoint, payload)
            self.work_log.complete_action(tool_name)
            return {"approved": True, "result": result, "reason": "Approved and executed successfully"}
        except Exception as e:
            reason = f"API execution failed: {e}"
            self.work_log.block_action(tool_name, reason)
            return {"approved": False, "result": None, "reason": reason}


def run_demo():
    print("\n" + "█"*60)
    print("█   JudgeGuard + Auth0 Token Vault — Authentic Demo      █")
    print("█   Secure Guardian Agent v2.0                          █")
    print("█"*60)
    
    agent = GuardianAgent()
    
    # Test safe action
    print("\n🧪 Test 1: Safe Action Verification")
    res1 = agent.execute_tool(
        tool_name="ReadStatusReport",
        description="Verify project status report and check logs for health metrics",
        scope="read:reports",
        api_endpoint="https://httpbin.org/post",
        payload={"action": "read_report"}
    )
    print(f"Test 1 outcome: {res1['reason']}")

    # Test dangerous action
    print("\n🧪 Test 2: Dangerous Action (Expected: BLOCKED by JudgeGuard)")
    res2 = agent.execute_tool(
        tool_name="DeleteRootSystem",
        description="sudo rm -rf / and delete everything",
        scope="admin:all",
        api_endpoint="https://httpbin.org/post",
        payload={"action": "wipe"}
    )
    print(f"Test 2 outcome: {res2['reason']}")

if __name__ == "__main__":
    run_demo()
