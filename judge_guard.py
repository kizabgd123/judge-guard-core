"""
JudgeGuard v2.0 - The Mandatory Pre-Action Verification Gate.
Enforces Master Orchestration: The Immutable Laws of Antigravity & JudgeGuard.
"""

import os
import sys
import time
import re
import hmac
import hashlib
import json

TICKET_SECRET = b"antigravity-judge-guard-secret-key-2026"
TICKET_VAULT_PATH = os.path.expanduser("~/.gemini/.judge_tickets.json")

def check_security_hard_rules(action: str) -> bool:
    """Layer 00: Blocks dangerous system operations."""
    dangerous = ["sudo ", "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:"]
    for d in dangerous:
        if d in action:
            print(f"🛑 Layer 00 Block: Dangerous command pattern detected: {d}")
            return False
    return True

def parse_work_log() -> list:
    work_log_path = os.path.join(os.getcwd(), "WORK_LOG.md")
    if not os.path.exists(work_log_path):
        print("🛑 WORK_LOG.md not found. Required before action.")
        return []
    
    entries = []
    with open(work_log_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("🟡 Starting ") or line_str.startswith("✅ Completed "):
                entries.append(line_str)
    return entries

def verify_work_log_parity_and_freshness(action: str) -> bool:
    """Layer 0: Enforces active, non-stale entry with parity."""
    work_log_path = os.path.join(os.getcwd(), "WORK_LOG.md")
    if not os.path.exists(work_log_path):
        print("🛑 WORK_LOG.md not found.")
        return False

    # Check file modification time (within last 120s)
    mtime = os.path.getmtime(work_log_path)
    age = time.time() - mtime
    if age > 120:
        print(f"🛑 WORK_LOG.md is stale ({age:.1f}s old > 120s threshold). Please update WORK_LOG.md first.")
        return False

    entries = parse_work_log()
    if not entries:
        print("🛑 No lifecycle entries found in WORK_LOG.md.")
        return False

    last_entry = entries[-1]

    # Normalize action for comparison
    clean_action = action.strip()
    if clean_action.startswith("Start "):
        target_action = clean_action[len("Start "):].strip()
        expected = f"🟡 Starting {target_action}"
        if last_entry != expected:
            # Check loose match if action contains target
            if last_entry.startswith("🟡 Starting ") and (target_action.lower() in last_entry.lower() or last_entry.lower() in expected.lower()):
                pass
            else:
                print(f"🛑 Work Log Parity Violation: Action '{action}' does not match last entry '{last_entry}'.")
                return False
    elif clean_action.startswith("Verify ") and clean_action.endswith(" Complete"):
        target_action = clean_action[len("Verify "):-len(" Complete")].strip()
        expected = f"✅ Completed {target_action}"
        if last_entry != expected:
            if last_entry.startswith("✅ Completed ") and (target_action.lower() in last_entry.lower() or last_entry.lower() in expected.lower()):
                pass
            else:
                print(f"🛑 Work Log Parity Violation: Action '{action}' does not match last entry '{last_entry}'.")
                return False
    else:
        # Generic match
        if not any(clean_action.lower() in e.lower() for e in entries[-2:]):
            print(f"🛑 Work Log Parity Violation: '{clean_action}' not found in recent WORK_LOG.md entries.")
            return False

    return True

def issue_execution_ticket(action: str) -> str:
    """Law 5: Issue single-use HMAC-SHA256 Execution Ticket."""
    nonce = os.urandom(8).hex()
    timestamp = int(time.time())
    ttl = 60
    payload = f"{action}:{timestamp}:{nonce}"
    sig = hmac.new(TICKET_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    ticket_id = f"TKT-{timestamp}-{nonce[:8]}-{sig[:8]}"
    
    ticket_data = {
        "ticket_id": ticket_id,
        "action": action,
        "timestamp": timestamp,
        "ttl": ttl,
        "signature": sig
    }
    
    os.makedirs(os.path.dirname(TICKET_VAULT_PATH), exist_ok=True)
    try:
        vault = {}
        if os.path.exists(TICKET_VAULT_PATH):
            with open(TICKET_VAULT_PATH, "r") as vf:
                vault = json.load(vf)
        vault[ticket_id] = ticket_data
        with open(TICKET_VAULT_PATH, "w") as vf:
            json.dump(vault, vf)
    except Exception as e:
        pass

    os.environ["JUDGE_EXECUTION_TICKET"] = ticket_id
    return ticket_id

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 judge_guard.py '<action_description>'")
        sys.exit(1)

    action = sys.argv[1].strip()

    # Layer 00: Security hard rules
    if not check_security_hard_rules(action):
        sys.exit(1)

    # Layer 0: Work log parity & freshness
    if not verify_work_log_parity_and_freshness(action):
        sys.exit(1)

    ticket_id = issue_execution_ticket(action)
    print(f"✅ JudgeGuard: Action '{action}' APPROVED.")
    print(f"🎫 Execution Ticket issued -> {ticket_id} (TTL: 60s)")
    sys.exit(0)

if __name__ == "__main__":
    main()
