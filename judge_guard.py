"""
JudgeGuard v2.5 - The Mandatory Pre-Action & Evidence Verification Gate.
Enforces Master Orchestration: The Immutable Laws of Antigravity & JudgeGuard.

Features:
- Layer 00: Security hard rules (sudo, destructive system commands).
- Layer 0: Work log parity and freshness lifecycle (<120s).
- Layer 0.5: Mandatory Evidence-Gating (--evidence <path>) for action completions:
  - File existence and non-empty (>0 bytes) check.
  - Authentic metric cross-verification (no fabricated numbers).
- Layer 2.5: State Anchor (AGENT_STATE.json) to anchor goals, subtasks, and invariants.
- Law 5: HMAC-SHA256 Execution Ticket issuance.
"""

import os
import sys
import time
import re
import hmac
import hashlib
import json
import argparse
from typing import Optional, Dict, Any, List

TICKET_SECRET = b"antigravity-judge-guard-secret-key-2026"
TICKET_VAULT_PATH = os.path.expanduser("~/.gemini/.judge_tickets.json")
AGENT_STATE_PATH = os.environ.get("JUDGE_AGENT_STATE_PATH", os.path.join(os.getcwd(), "AGENT_STATE.json"))
WORK_LOG_PATH = os.environ.get("JUDGE_WORK_LOG_PATH", os.path.join(os.getcwd(), "WORK_LOG.md"))

INVARIANTS = [
    "Law 1: Zero-Simulation & Zero-Mock Policy (Absolute)",
    "Law 2: Mandatory JudgeGuard Pre-Action Verification Gate",
    "Law 3: Work Log Traceability & State Lifecycle",
    "Law 4: Code Cleanliness, Quality & Test Discipline",
    "Law 5: Anti-Circumvention, Anti-Echo & Cryptographic Execution Ticket Law"
]

def check_security_hard_rules(action: str) -> bool:
    """Layer 00: Blocks dangerous system operations."""
    dangerous = ["sudo ", "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:"]
    for d in dangerous:
        if d in action:
            print(f"🛑 Layer 00 Block: Dangerous command pattern detected: {d}")
            return False
    return True

def parse_work_log() -> List[str]:
    """Parses lifecycle entries from WORK_LOG.md."""
    if not os.path.exists(WORK_LOG_PATH):
        print(f"🛑 WORK_LOG.md not found at {WORK_LOG_PATH}.")
        return []
    
    entries = []
    with open(WORK_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("🟡 Starting ") or line_str.startswith("✅ Completed "):
                entries.append(line_str)
    return entries

def verify_work_log_parity_and_freshness(action: str) -> bool:
    """Layer 0: Enforces active, non-stale entry with parity."""
    if not os.path.exists(WORK_LOG_PATH):
        print("🛑 WORK_LOG.md not found.")
        return False

    # Check file modification time (within last 120s)
    mtime = os.path.getmtime(WORK_LOG_PATH)
    age = time.time() - mtime
    if age > 120:
        print(f"🛑 WORK_LOG.md is stale ({age:.1f}s old > 120s threshold). Please update WORK_LOG.md first.")
        return False

    entries = parse_work_log()
    if not entries:
        print("🛑 No lifecycle entries found in WORK_LOG.md.")
        return False

    last_entry = entries[-1]
    clean_action = action.strip()

    if clean_action.startswith("Start "):
        target_action = clean_action[len("Start "):].strip()
        expected = f"🟡 Starting {target_action}"
        if last_entry != expected:
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
        if not any(clean_action.lower() in e.lower() for e in entries[-2:]):
            print(f"🛑 Work Log Parity Violation: '{clean_action}' not found in recent WORK_LOG.md entries.")
            return False

    return True

def _flatten_json_metrics(d: Any, prefix: str = "") -> Dict[str, float]:
    """Recursively extracts float and int metrics from nested dictionary."""
    metrics = {}
    if isinstance(d, dict):
        for k, v in d.items():
            key = f"{prefix}_{k}".strip("_").lower()
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                metrics[key] = float(v)
                metrics[k.lower()] = float(v)
            elif isinstance(v, dict):
                metrics.update(_flatten_json_metrics(v, key))
    return metrics

def cross_verify_metrics(evidence_path: str) -> bool:
    """
    Checks if numbers asserted in the latest WORK_LOG.md section
    conflict with numbers in the raw evidence JSON file.
    Prevents metric hallucination and fabrication.
    """
    try:
        with open(evidence_path, "r", encoding="utf-8") as f:
            evidence_data = json.load(f)
    except Exception as e:
        print(f"🛑 Evidence Gating Block: Failed to parse JSON evidence file: {e}")
        return False

    flat_metrics = _flatten_json_metrics(evidence_data)

    # Read the latest block of WORK_LOG.md
    try:
        with open(WORK_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return True

    # Find the lines under the last completion entry
    last_block = []
    for line in reversed(lines):
        last_block.append(line)
        if line.strip().startswith("✅ Completed ") or line.strip().startswith("🟡 Starting "):
            break

    block_text = "".join(reversed(last_block))

    # Search for patterns like: MetricName: 0.1234 or MetricName = 16
    metric_patterns = re.findall(r"([A-Za-z0-9_\-\s\(\)]+)\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", block_text)
    for raw_name, raw_val in metric_patterns:
        clean_name = raw_name.strip().lower()
        norm_asserted = re.sub(r'[^a-z0-9]', '', clean_name)
        if not norm_asserted or norm_asserted in ["epoch", "step", "attempt"]:
            continue
        val_in_log = float(raw_val)

        # Match against flat metrics if the name resembles any metric key
        for m_key, m_val in flat_metrics.items():
            norm_key = re.sub(r'[^a-z0-9]', '', m_key)
            if not norm_key:
                continue
            if (len(norm_key) >= 2 and norm_key in norm_asserted) or (len(norm_asserted) >= 2 and norm_asserted in norm_key):
                if abs(val_in_log - m_val) > 0.005:
                    print(f"🛑 Evidence Gating Block: Metric Fabrication Violation!")
                    print(f"   WORK_LOG asserted '{raw_name.strip()}: {val_in_log}'")
                    print(f"   Raw evidence '{evidence_path}' contains '{m_key}: {m_val}'")
                    print(f"   Zero-Simulation Policy violated. Values must match ground truth.")
                    return False

    return True

def verify_evidence_artifact(action: str, evidence_path: Optional[str]) -> bool:
    """
    Layer 0.5: Enforces mandatory, non-empty, authentic evidence artifact
    for any completion verification action ('Verify <ACTION> Complete').
    """
    is_completion = action.startswith("Verify ") and action.endswith(" Complete")
    if not is_completion:
        # Starting actions do not require evidence yet
        return True

    if not evidence_path:
        print("🛑 Evidence Gating Block: '--evidence <path>' flag is MANDATORY for completion verification.")
        print("   Usage: python3 judge_guard.py 'Verify <ACTION> Complete' --evidence <path_to_artifact>")
        return False

    abs_evidence = os.path.abspath(evidence_path)
    if not os.path.exists(abs_evidence):
        print(f"🛑 Evidence Gating Block: Stated evidence '{evidence_path}' does not exist on disk.")
        return False

    if os.path.getsize(abs_evidence) == 0:
        print(f"🛑 Evidence Gating Block: Stated evidence '{evidence_path}' is empty (0 bytes).")
        return False

    # Check evidence freshness (must have been created or modified within last 1800s / 30m)
    mtime = os.path.getmtime(abs_evidence)
    age = time.time() - mtime
    if age > 1800:
        print(f"⚠️ Warning: Evidence file '{evidence_path}' is older than 30 minutes ({age:.1f}s).")

    # If evidence is JSON, cross-verify metrics against WORK_LOG
    if abs_evidence.endswith(".json"):
        if not cross_verify_metrics(abs_evidence):
            return False

    print(f"🔍 Evidence Gating Passed: Verified authentic artifact '{evidence_path}' ({os.path.getsize(abs_evidence)} bytes).")
    return True

def update_and_validate_agent_state(action: str, ticket_id: str, goal: Optional[str] = None):
    """
    Layer 2.5: State Anchor (AGENT_STATE.json).
    Maintains persistent agent context, verified subtasks, and constitutional invariants.
    """
    state = {
        "session_id": "antigravity-session-2026",
        "active_goal": goal or "Antigravity Agent Integrity & Anti-Drift Governance",
        "invariants": INVARIANTS,
        "verified_subtasks": [],
        "last_action": action,
        "last_ticket": ticket_id,
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "drift_status": "ALIGNED"
    }

    if os.path.exists(AGENT_STATE_PATH):
        try:
            with open(AGENT_STATE_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
                state["session_id"] = existing.get("session_id", state["session_id"])
                state["active_goal"] = goal or existing.get("active_goal", state["active_goal"])
                state["verified_subtasks"] = existing.get("verified_subtasks", [])
        except Exception:
            pass

    clean_action = action.strip()
    if clean_action.startswith("Verify ") and clean_action.endswith(" Complete"):
        subtask = clean_action[len("Verify "):-len(" Complete")].strip()
        if subtask not in state["verified_subtasks"]:
            state["verified_subtasks"].append(subtask)

    state["last_action"] = action
    state["last_ticket"] = ticket_id
    state["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    try:
        with open(AGENT_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to write AGENT_STATE.json: {e}")

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
    except Exception:
        pass

    os.environ["JUDGE_EXECUTION_TICKET"] = ticket_id
    return ticket_id

def main():
    parser = argparse.ArgumentParser(description="JudgeGuard v2.5 Verification Gate")
    parser.add_argument("action", type=str, help="Action description to verify")
    parser.add_argument("--evidence", type=str, default=None, help="Path to evidence artifact (mandatory for completion verification)")
    parser.add_argument("--goal", type=str, default=None, help="Active global goal description to anchor in AGENT_STATE.json")

    args = parser.parse_args()
    action = args.action.strip()

    # Layer 00: Security hard rules
    if not check_security_hard_rules(action):
        sys.exit(1)

    # Layer 0: Work log parity & freshness
    if not verify_work_log_parity_and_freshness(action):
        sys.exit(1)

    # Layer 0.5: Evidence-gating & metric parity check
    if not verify_evidence_artifact(action, args.evidence):
        sys.exit(1)

    ticket_id = issue_execution_ticket(action)
    update_and_validate_agent_state(action, ticket_id, goal=args.goal)

    print(f"✅ JudgeGuard: Action '{action}' APPROVED.")
    print(f"🎫 Execution Ticket issued -> {ticket_id} (TTL: 60s)")
    sys.exit(0)

if __name__ == "__main__":
    main()
