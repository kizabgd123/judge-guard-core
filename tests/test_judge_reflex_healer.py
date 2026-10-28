import os
import sys
import json
import time
import pytest

from scripts.judge_reflex_healer import (
    classify_guard_failure,
    emit_guard_alert,
    load_constitution_rules,
    heal_work_log_freshness,
    heal_work_log_parity,
    verify_with_reflex,
    write_step_summary,
    GUARD_ALERT_PATH,
    WORK_LOG_PATH
)


def test_classify_guard_failure():
    assert classify_guard_failure("🛑 Layer 00 Block: Dangerous command pattern detected: sudo") == "SECURITY_HARD_RULE"
    assert classify_guard_failure("🛑 WORK_LOG.md is stale (150.0s old > 120s threshold).") == "WORK_LOG_STALE"
    assert classify_guard_failure("🛑 Work Log Parity Violation: Action 'X' does not match last entry 'Y'.") == "PARITY_VIOLATION"
    assert classify_guard_failure("🛑 No lifecycle entries found in WORK_LOG.md.") == "NO_LIFECYCLE_ENTRIES"
    assert classify_guard_failure("Some completely unknown string") == "UNKNOWN_ERROR"


def test_guard_alert_schema_section48():
    alert = emit_guard_alert(
        failure_type="WORK_LOG_STALE",
        action="Start Test Action",
        details="WORK_LOG.md is stale (130s)",
        attempt=0
    )
    assert alert["domain_context"] == "CI/CD & Pre-Action Governance"
    assert alert["tactic_id"] == "TAC-CONSTITUTION-SEC48"
    assert alert["severity"] in ["INFO", "WARNING", "VETO", "HALT"]
    assert alert["actionable_fallback"] == "refresh_work_log_timestamp"
    assert alert["recoverable"] is True
    assert "Logic Hint" not in alert  # schema uses logic_hint key
    assert len(alert["logic_hint"]) > 0
    assert os.path.exists(GUARD_ALERT_PATH)

    with open(GUARD_ALERT_PATH, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["action"] == "Start Test Action"


def test_security_hard_rule_unrecoverable():
    alert = emit_guard_alert(
        failure_type="SECURITY_HARD_RULE",
        action="sudo rm -rf /",
        details="Layer 00 Block",
        attempt=0
    )
    assert alert["severity"] == "HALT"
    assert alert["recoverable"] is False
    assert alert["actionable_fallback"] == "halt_immediately"


def test_heal_work_log_freshness(tmp_path, monkeypatch):
    test_log = tmp_path / "WORK_LOG.md"
    test_log.write_text("🟡 Starting test freshness\n", encoding="utf-8")

    # Set old mtime (300 seconds ago)
    old_time = time.time() - 300
    os.utime(test_log, (old_time, old_time))
    assert time.time() - os.path.getmtime(test_log) > 250

    monkeypatch.setattr("scripts.judge_reflex_healer.WORK_LOG_PATH", str(test_log))
    success = heal_work_log_freshness()
    assert success is True
    # Now fresh mtime
    assert time.time() - os.path.getmtime(test_log) < 5


def test_heal_work_log_parity(tmp_path, monkeypatch):
    test_log = tmp_path / "WORK_LOG.md"
    test_log.write_text("🟡 Starting Old Action\n", encoding="utf-8")

    monkeypatch.setattr("scripts.judge_reflex_healer.WORK_LOG_PATH", str(test_log))
    success = heal_work_log_parity("Start New Target Action")
    assert success is True

    content = test_log.read_text(encoding="utf-8")
    assert "🟡 Starting New Target Action" in content.splitlines()[-1]


def test_write_step_summary(tmp_path, monkeypatch):
    summary_file = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    alert = {
        "failure_type": "PARITY_VIOLATION",
        "severity": "WARNING",
        "actionable_fallback": "reconcile_starting_entry",
        "logic_hint": "Disparity reconciled automatically."
    }

    write_step_summary("REFLEX_HEALED", "Start Reflex Action", alert)
    assert summary_file.exists()
    content = summary_file.read_text(encoding="utf-8")
    assert "JudgeGuard Autonomous CI Verification Report" in content
    assert "Autonomous Reflexive Self-Healing Succeeded" in content
