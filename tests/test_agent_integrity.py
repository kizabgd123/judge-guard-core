"""
Unit and integration tests for Antigravity Agent Integrity, Evidence-Gating,
Metric Parity Verification, and State Anchor (AGENT_STATE.json).
"""

import os
import sys
import json
import time
import subprocess
import pytest
from pathlib import Path

def test_evidence_gating_missing_flag_blocks_completion(tmp_path):
    """Verifies that attempting completion verification without --evidence is strictly blocked."""
    work_log = tmp_path / "WORK_LOG.md"
    action_text = "Test Integrity Subtask 1"
    work_log.write_text(f"🟡 Starting {action_text}\n✅ Completed {action_text}\n")

    cmd = [
        sys.executable,
        "judge_guard.py",
        f"Verify {action_text} Complete"
    ]
    env = os.environ.copy()
    env["JUDGE_WORK_LOG_PATH"] = str(work_log)
    
    proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    assert proc.returncode != 0
    assert "Evidence Gating Block" in proc.stdout
    assert "--evidence <path>" in proc.stdout

def test_evidence_gating_nonexistent_file_blocks(tmp_path):
    """Verifies that pointing --evidence to a non-existent file is strictly blocked."""
    work_log = tmp_path / "WORK_LOG.md"
    action_text = "Test Nonexistent Artifact"
    work_log.write_text(f"🟡 Starting {action_text}\n✅ Completed {action_text}\n")

    cmd = [
        sys.executable,
        "judge_guard.py",
        f"Verify {action_text} Complete",
        "--evidence",
        "/tmp/definitely_nonexistent_artifact_xyz123.json"
    ]
    env = os.environ.copy()
    env["JUDGE_WORK_LOG_PATH"] = str(work_log)

    proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode != 0
    assert "does not exist on disk" in proc.stdout

def test_evidence_gating_empty_file_blocks(tmp_path):
    """Verifies that an empty (0 bytes) evidence file is strictly blocked."""
    work_log = tmp_path / "WORK_LOG.md"
    action_text = "Test Empty Artifact"
    work_log.write_text(f"🟡 Starting {action_text}\n✅ Completed {action_text}\n")

    empty_file = tmp_path / "empty_evidence.txt"
    empty_file.write_text("")

    cmd = [
        sys.executable,
        "judge_guard.py",
        f"Verify {action_text} Complete",
        "--evidence",
        str(empty_file)
    ]
    env = os.environ.copy()
    env["JUDGE_WORK_LOG_PATH"] = str(work_log)

    proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode != 0
    assert "is empty (0 bytes)" in proc.stdout

def test_metric_parity_disparity_blocks(tmp_path):
    """
    Verifies Law 1 Zero-Simulation Policy:
    Asserting metrics in WORK_LOG that conflict with raw evidence JSON must be blocked.
    """
    evidence_json = tmp_path / "raw_eval_metrics.json"
    evidence_json.write_text(json.dumps({
        "panoptic_quality_pq": 0.0,
        "segmentation_quality_sq": 0.0,
        "full_disk_dice": 0.0076
    }))

    from judge_guard import cross_verify_metrics
    import judge_guard

    temp_work_log = tmp_path / "WORK_LOG.md"
    temp_work_log.write_text(
        "🟡 Starting Phase Eval\n"
        "✅ Completed Phase Eval\n"
        "- Mean Panoptic Quality (PQ): 0.8542\n"
        "- Mean Full-Disk Dice: 0.9120\n"
    )

    orig_path = judge_guard.WORK_LOG_PATH
    try:
        judge_guard.WORK_LOG_PATH = str(temp_work_log)
        match_result = cross_verify_metrics(str(evidence_json))
        assert match_result is False
    finally:
        judge_guard.WORK_LOG_PATH = orig_path

def test_metric_parity_exact_match_passes(tmp_path):
    """Verifies that when metrics in WORK_LOG match raw evidence JSON, verification succeeds."""
    evidence_json = tmp_path / "raw_eval_metrics.json"
    evidence_json.write_text(json.dumps({
        "panoptic_quality_pq": 0.0,
        "dice": 0.0076
    }))

    temp_work_log = tmp_path / "WORK_LOG.md"
    temp_work_log.write_text(
        "🟡 Starting Phase Eval\n"
        "✅ Completed Phase Eval\n"
        "- Mean Panoptic Quality (PQ): 0.0\n"
        "- Full-Disk Dice: 0.0076\n"
    )

    from judge_guard import cross_verify_metrics
    import judge_guard

    orig_path = judge_guard.WORK_LOG_PATH
    try:
        judge_guard.WORK_LOG_PATH = str(temp_work_log)
        match_result = cross_verify_metrics(str(evidence_json))
        assert match_result is True
    finally:
        judge_guard.WORK_LOG_PATH = orig_path

def test_agent_state_anchor_records_subtasks(tmp_path):
    """Verifies that AGENT_STATE.json maintains persistent state anchor across actions."""
    state_file = tmp_path / "AGENT_STATE.json"
    
    import judge_guard
    orig_state_path = judge_guard.AGENT_STATE_PATH
    try:
        judge_guard.AGENT_STATE_PATH = str(state_file)
        judge_guard.update_and_validate_agent_state(
            action="Verify Subtask Alpha Complete",
            ticket_id="TKT-TEST-1234",
            goal="Ensure Total Antigravity Integrity"
        )
        assert state_file.exists()
        with open(state_file, "r") as f:
            data = json.load(f)
            assert data["active_goal"] == "Ensure Total Antigravity Integrity"
            assert "Subtask Alpha" in data["verified_subtasks"]
            assert data["last_ticket"] == "TKT-TEST-1234"
            assert len(data["invariants"]) == 5
    finally:
        judge_guard.AGENT_STATE_PATH = orig_state_path
