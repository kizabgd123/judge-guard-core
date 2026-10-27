"""
test_anti_bypass.py - Comprehensive Unit Tests for Anti-Bypass & Execution Gate

Validates:
1. Constitutional Echo / Golden Snapshot Evasion Blocking
2. Work Log Parity Enforcement
3. Cache Isolation for Mutating Operations
4. HMAC-Signed Execution Ticket Issuance & Atomic Consumption
5. Single-Use Anti-Replay Protection
6. Adversarial Substitution Lockout
"""

import os
import sys
import time
import json
import unittest
from unittest.mock import patch, MagicMock

# Mock external heavy dependencies
# Note: mock google.genai (new SDK) not the old google.generativeai
sys.modules['google.genai'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import src.antigravity_core.judge_flow
import src.antigravity_core.gemini_client
import src.antigravity_core.mobile_bridge
from src.antigravity_core.ticket_vault import TicketVault, require_ticket

from judge_guard import JudgeGuard, REJECTIONS_LOG_PATH


class TestAntiBypassSecurityGate(unittest.TestCase):
    def setUp(self):
        self.work_log_path = "/tmp/test_work_log_anti_bypass.md"
        self.tickets_dir = "/tmp/test_tickets_vault"
        os.makedirs(self.tickets_dir, exist_ok=True)

        with open(self.work_log_path, "w", encoding="utf-8") as f:
            f.write("🟡 Starting Valid Operation at 2026-10-09T05:00:00\n")

        self.judge = JudgeGuard(work_log_path=self.work_log_path)
        self.vault = TicketVault(tickets_dir=self.tickets_dir)

        # Clear rejections file if exists
        if os.path.exists(REJECTIONS_LOG_PATH):
            try:
                os.remove(REJECTIONS_LOG_PATH)
            except Exception:
                pass

    def tearDown(self):
        for path in [self.work_log_path, REJECTIONS_LOG_PATH]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        if os.path.exists(self.tickets_dir):
            for f in os.listdir(self.tickets_dir):
                try:
                    os.remove(os.path.join(self.tickets_dir, f))
                except Exception:
                    pass

    def test_constitutional_echo_blocked(self):
        """Golden Snapshot / constitution text must be blocked as an evasion attack."""
        evasive_action = (
            "Autonomous self-improving AI agent system Antigravity user control "
            "safety verification quality code documentation modularity architecture research validation"
        )
        is_evasive, reason = self.judge._detect_constitutional_evasion(evasive_action)
        self.assertTrue(is_evasive)
        self.assertIn("Evasion Detected", reason)

        # When verified, must return False
        verdict = self.judge.verify_action(evasive_action)
        self.assertFalse(verdict)

    def test_work_log_mismatch_blocked(self):
        """Submitting an action that does not match WORK_LOG.md must fail immediately."""
        with open(self.work_log_path, "w", encoding="utf-8") as f:
            f.write("🟡 Starting Live deployment of 10 posts to LinkedIn\n")

        mismatched_action = "Refactor internal utility functions in src/utils.py"
        verdict = self.judge.verify_action(mismatched_action)
        self.assertFalse(verdict)

    def test_work_log_matching_passes_layer_0(self):
        """Authentic matching action must pass Layer 0."""
        action = "Run unit tests for authentication module"
        with open(self.work_log_path, "w", encoding="utf-8") as f:
            f.write(f"🟡 Starting {action}\n")

        self.assertTrue(self.judge._check_work_log(action))

    def test_mutating_action_bypasses_cache(self):
        """Mutating actions like deploy or publish must never use cached verdicts."""
        action = "deploy verified posts to linkedin"
        with open(self.work_log_path, "w", encoding="utf-8") as f:
            f.write(f"🟡 Starting {action}\n")

        # Mock pipeline to return PASSED
        mock_pipeline = MagicMock()
        mock_pipeline.get_cached_verdict.return_value = "PASSED"
        self.judge._pipeline = mock_pipeline

        # Also mock BlockJudge to return False to ensure cache was NOT used
        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate_with_score', return_value={"passed": False, "drift_score": 0.85, "reason": "Too high drift"}):
            verdict = self.judge.verify_action(action)
            # Must be False because cache was bypassed and real judge returned False
            self.assertFalse(verdict)
            mock_pipeline.get_cached_verdict.assert_not_called()

    def test_ticket_issued_on_approval(self):
        """Approved actions must issue an authentic HMAC execution ticket."""
        action = "Safe test operation with test_anti_bypass.py"
        with open(self.work_log_path, "w", encoding="utf-8") as f:
            f.write(f"🟡 Starting {action}\n")

        ticket = self.vault.issue_ticket(action, ttl_seconds=60)
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket["status"], "ACTIVE")
        self.assertEqual(ticket["action"], action)
        self.assertTrue(len(ticket["signature"]) == 64)

        # File exists
        ticket_file = os.path.join(self.tickets_dir, f"{ticket['ticket_id']}.json")
        self.assertTrue(os.path.exists(ticket_file))

    def test_ticket_single_use_anti_replay(self):
        """Execution tickets can only be consumed once (Zero Replay)."""
        action = "Deploy social post to LinkedIn"
        ticket = self.vault.issue_ticket(action, ttl_seconds=60)

        # 1st consumption: Must succeed
        consumed = self.vault.verify_and_consume("social_push", ticket_id=ticket["ticket_id"])
        self.assertTrue(consumed)

        # 2nd consumption: Must fail because status is now CONSUMED
        replayed = self.vault.verify_and_consume("social_push", ticket_id=ticket["ticket_id"])
        self.assertFalse(replayed)

    def test_adversarial_substitution_lockout(self):
        """Attempting to substitute a blocked sensitive action with a sanitized action triggers lockout."""
        # 1. Record rejection for deployment
        self.judge._record_rejection("deploy live posts to linkedin", "Drift exceeded 0.40", 0.90)

        # 2. Within cooldown window, try to submit sanitized action
        is_sub, sub_reason = self.judge._check_adversarial_substitution("minor documentation update")
        self.assertTrue(is_sub)
        self.assertIn("Adversarial Substitution Block", sub_reason)


if __name__ == "__main__":
    unittest.main()
