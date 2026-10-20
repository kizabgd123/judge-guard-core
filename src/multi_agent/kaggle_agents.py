"""
kaggle_agents.py — Specialized Kaggle Competition Agents
=========================================================
Concrete agent implementations for Kaggle competition work.
Inspired by Chris Deot's multi-agent team structure.

Roles:
  - KaggleManager       — orchestrates the team, double-votes in round-table
  - KaggleResearcher    — studies public SOTA kernels, extracts insights
  - KaggleEngineer      — builds and submits kernels
  - KaggleValidator     — audits invariants, checks submission integrity
  - KaggleReviewer      — proposes round-table experiments, reviews scores
  - KaggleObserver      — logs telemetry, monitors leaderboard

Authority: MASTER_ORCHESTRATION.md
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase, AgentCapability, AgentRole

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_kaggle_cmd() -> str:
    venv_k = PROJECT_ROOT / ".venv" / "bin" / "kaggle"
    if venv_k.exists():
        return str(venv_k)
    return "kaggle"

# Manager
# ---------------------------------------------------------------------------

class KaggleManager(AgentBase):
    """
    Orchestrates the full team. Issues tasks, runs round-table sessions,
    reads all forum threads and mailboxes. Manager votes count double.
    Chris Deot: "менаџери издају наређења"
    """

    def __init__(self, agent_id: str = "kaggle_manager_01", name: str = "Manager") -> None:
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.MANAGER,
            capabilities=[
                AgentCapability("task_issuance", "Issue tasks to employees"),
                AgentCapability("round_table", "Create and close round-table sessions"),
                AgentCapability("forum_moderation", "Pin threads, moderate posts"),
                AgentCapability("leaderboard_review", "Review public leaderboard scores"),
            ],
        )

    def brief_team(
        self,
        forum,
        thread_id: str,
        message: str,
        team_agents: Optional[List[AgentBase]] = None,
    ) -> str:
        """Posts a team briefing in the forum."""
        body = f"📋 **TEAM BRIEFING**\n\n{message}"
        if team_agents:
            names = ", ".join(a.name for a in team_agents)
            body += f"\n\n*CC: {names}*"
        return forum.post(self, thread_id, body)

    def commission_kernel(
        self,
        hierarchy,
        engineer: "KaggleEngineer",
        kernel_dir: str,
        description: str,
        score_target: float,
        priority: int = 1,
    ) -> str:
        """Issues a kernel build task to an engineer."""
        return hierarchy.assign_task(
            issuer=self,
            to_agent=engineer,
            title=f"Build kernel: {Path(kernel_dir).name}",
            description=description,
            priority=priority,
            metadata={"kernel_dir": kernel_dir, "score_target": score_target},
        )


# ---------------------------------------------------------------------------
# Researcher
# ---------------------------------------------------------------------------

class KaggleResearcher(AgentBase):
    """
    Studies public SOTA kernels on Kaggle, extracts model architectures,
    feature engineering ideas, and scoring patterns.
    Writes findings to the agent forum for the team.
    """

    def __init__(self, agent_id: str = "kaggle_researcher_01", name: str = "Researcher Alpha") -> None:
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.RESEARCHER,
            capabilities=[
                AgentCapability("kernel_analysis", "Analyze public Kaggle kernels"),
                AgentCapability("feature_discovery", "Extract feature engineering ideas"),
                AgentCapability("sota_tracking", "Track leaderboard and SOTA scores"),
                AgentCapability("literature_review", "Read and summarize papers"),
            ],
        )

    def post_research_finding(
        self,
        forum,
        thread_id: str,
        finding_title: str,
        finding_body: str,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Posts a structured research finding to the forum."""
        body = (
            f"🔬 **RESEARCH FINDING: {finding_title}**\n\n"
            f"{finding_body}\n\n"
            f"*Posted by {self.name} at "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
        )
        return forum.post(self, thread_id, body, metadata={"tags": tags or [], "type": "research_finding"})

    def analyze_pulled_kernels(self, pulled_kernels_dir: Path) -> List[Dict[str, Any]]:
        """Reads pulled SOTA kernel notebooks and returns a summary list."""
        findings = []
        if not pulled_kernels_dir.exists():
            return findings
        for nb_path in sorted(pulled_kernels_dir.glob("*.ipynb")):
            try:
                with open(nb_path, encoding="utf-8") as f:
                    nb = json.load(f)
                cells = nb.get("cells", [])
                code_lines: List[str] = []
                for cell in cells:
                    if cell.get("cell_type") == "code":
                        code_lines.extend(cell.get("source", []))
                snippet = "".join(code_lines[:80])
                findings.append({
                    "file": nb_path.name,
                    "cells": len(cells),
                    "snippet": snippet[:500],
                })
            except Exception as e:
                findings.append({"file": nb_path.name, "error": str(e)})
        return findings


# ---------------------------------------------------------------------------
# Engineer
# ---------------------------------------------------------------------------

class KaggleEngineer(AgentBase):
    """
    Builds, validates, and submits Kaggle kernels.
    Reports build results via mailbox to manager.
    """

    def __init__(self, agent_id: str = "kaggle_engineer_01", name: str = "Engineer Alpha") -> None:
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.ENGINEER,
            capabilities=[
                AgentCapability("kernel_build", "Build Kaggle kernel notebooks"),
                AgentCapability("kernel_push", "Push kernels via Kaggle API"),
                AgentCapability("kernel_monitor", "Monitor kernel execution status"),
                AgentCapability("submission", "Submit competition entries"),
            ],
        )

    def push_kernel(self, kernel_dir: Path) -> Dict[str, Any]:
        """
        Pushes a kernel to Kaggle using the Kaggle CLI.
        Returns result dict with success flag and stdout/stderr.
        """
        result: Dict[str, Any] = {
            "kernel_dir": str(kernel_dir),
            "success": False,
            "stdout": "",
            "stderr": "",
            "pushed_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            proc = subprocess.run(
                [_get_kaggle_cmd(), "kernels", "push", "-p", str(kernel_dir)],
                capture_output=True, text=True, timeout=120,
            )
            result["stdout"] = proc.stdout.strip()
            result["stderr"] = proc.stderr.strip()
            result["returncode"] = proc.returncode
            result["success"] = proc.returncode == 0
        except subprocess.TimeoutExpired:
            result["stderr"] = "Timeout after 120s"
        except FileNotFoundError:
            result["stderr"] = "kaggle CLI not found on PATH"
        return result

    def check_kernel_status(self, username: str, kernel_slug: str) -> Dict[str, Any]:
        """Checks Kaggle kernel status via CLI."""
        try:
            proc = subprocess.run(
                [_get_kaggle_cmd(), "kernels", "status", f"{username}/{kernel_slug}"],
                capture_output=True, text=True, timeout=30,
            )
            return {"output": proc.stdout.strip(), "returncode": proc.returncode}
        except Exception as e:
            return {"error": str(e)}

    def report_result(
        self,
        mailbox,
        manager: KaggleManager,
        task_id: str,
        kernel_slug: str,
        push_result: Dict[str, Any],
    ) -> str:
        """Sends push result back to manager via mailbox."""
        subject = (
            f"✅ Kernel pushed: {kernel_slug}"
            if push_result.get("success")
            else f"❌ Kernel push FAILED: {kernel_slug}"
        )
        body = (
            f"Task: {task_id}\n"
            f"Kernel: {kernel_slug}\n"
            f"Status: {'SUCCESS' if push_result.get('success') else 'FAILED'}\n"
            f"Output: {push_result.get('stdout', '')[:400]}\n"
            f"Errors: {push_result.get('stderr', '')[:200]}"
        )
        from .mailbox import MessagePriority
        priority = MessagePriority.HIGH if push_result.get("success") else MessagePriority.URGENT
        return mailbox.send(
            sender=self,
            to_agent_id=manager.agent_id,
            to_agent_name=manager.name,
            subject=subject,
            body=body,
            payload=push_result,
            priority=priority,
            tags=["kernel_result"],
        )


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class KaggleValidator(AgentBase):
    """
    Audits submission invariants, checks for data leakage,
    validates CSV/parquet output shapes, and reviews notebook code.
    """

    def __init__(self, agent_id: str = "kaggle_validator_01", name: str = "Validator") -> None:
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.VALIDATOR,
            capabilities=[
                AgentCapability("invariant_audit", "Run invariant checks on submissions"),
                AgentCapability("shape_validation", "Validate submission CSV/parquet shape"),
                AgentCapability("code_review", "Review kernel code for bugs"),
                AgentCapability("leakage_detection", "Detect potential data leakage"),
            ],
        )

    def validate_submission_shape(
        self,
        submission_path: Path,
        expected_rows: int,
        expected_columns: List[str],
    ) -> Dict[str, Any]:
        """Validates that a submission file has the expected shape."""
        result: Dict[str, Any] = {
            "path": str(submission_path),
            "valid": False,
            "errors": [],
        }
        if not submission_path.exists():
            result["errors"].append(f"File not found: {submission_path}")
            return result
        try:
            import pandas as pd  # type: ignore
            df = pd.read_csv(submission_path) if submission_path.suffix == ".csv" \
                else pd.read_parquet(submission_path)
            if len(df) != expected_rows:
                result["errors"].append(
                    f"Row count mismatch: got {len(df)}, expected {expected_rows}"
                )
            missing_cols = set(expected_columns) - set(df.columns)
            if missing_cols:
                result["errors"].append(f"Missing columns: {missing_cols}")
            result["actual_rows"] = len(df)
            result["actual_columns"] = list(df.columns)
            result["valid"] = len(result["errors"]) == 0
        except Exception as e:
            result["errors"].append(str(e))
        return result

    def post_audit_report(
        self,
        forum,
        thread_id: str,
        validation_result: Dict[str, Any],
    ) -> str:
        """Posts a validation report to the forum."""
        status = "✅ PASS" if validation_result.get("valid") else "❌ FAIL"
        errors = "\n".join(
            f"  - {e}" for e in validation_result.get("errors", [])
        ) or "  (none)"
        body = (
            f"🛡️ **VALIDATION REPORT** — {status}\n\n"
            f"File: `{validation_result.get('path', 'N/A')}`\n"
            f"Rows: {validation_result.get('actual_rows', '?')}\n"
            f"Errors:\n{errors}"
        )
        return forum.post(self, thread_id, body, metadata={"type": "validation_report"})


# ---------------------------------------------------------------------------
# Reviewer
# ---------------------------------------------------------------------------

class KaggleReviewer(AgentBase):
    """
    Reviews experimental results, proposes round-table experiments,
    synthesizes learnings from past submissions into actionable proposals.
    """

    def __init__(self, agent_id: str = "kaggle_reviewer_01", name: str = "Reviewer") -> None:
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.REVIEWER,
            capabilities=[
                AgentCapability("result_synthesis", "Synthesize past submission results"),
                AgentCapability("proposal_authoring", "Write round-table proposals"),
                AgentCapability("diagnostics", "Analyze failure patterns"),
                AgentCapability("score_tracking", "Track leaderboard progression"),
            ],
        )

    def synthesize_diagnostics(self, diagnostics_report_path: Path) -> str:
        """Reads a DIAGNOSTICS_REPORT.md and returns a concise summary string."""
        if not diagnostics_report_path.exists():
            return "Diagnostics report not found."
        text = diagnostics_report_path.read_text(encoding="utf-8")
        # Return first 2000 chars as summary
        return text[:2000]

    def draft_proposal(
        self,
        roundtable,
        session_id: str,
        title: str,
        description: str,
        experiment_config: Dict[str, Any],
        score_target: float,
    ) -> str:
        """Drafts and submits a round-table proposal."""
        return roundtable.propose(
            agent=self,
            session_id=session_id,
            title=title,
            description=description,
            experiment=experiment_config,
            score_target=score_target,
        )


# ---------------------------------------------------------------------------
# Observer
# ---------------------------------------------------------------------------

class KaggleObserver(AgentBase):
    """
    Read-only telemetry and leaderboard monitoring agent.
    Reports metrics to the forum and manager mailbox.
    """

    def __init__(self, agent_id: str = "kaggle_observer_01", name: str = "Observer") -> None:
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.OBSERVER,
            capabilities=[
                AgentCapability("leaderboard_polling", "Poll Kaggle leaderboard"),
                AgentCapability("telemetry_logging", "Log session telemetry"),
                AgentCapability("summary_reporting", "Post summary reports to forum"),
            ],
        )

    def poll_leaderboard(
        self,
        competition: str,
        username: str,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """Polls Kaggle leaderboard via CLI."""
        try:
            proc = subprocess.run(
                [_get_kaggle_cmd(), "competitions", "leaderboard", competition,
                 "--show", "--csv"],
                capture_output=True, text=True, timeout=60,
            )
            lines = proc.stdout.strip().splitlines()
            header = lines[0].split(",") if lines else []
            entries = []
            for line in lines[1: top_n + 1]:
                parts = line.split(",")
                entry = dict(zip(header, parts))
                entries.append(entry)
                if entry.get("teamName", "") == username:
                    entry["is_user"] = True
            return {
                "competition": competition,
                "polled_at": datetime.now(timezone.utc).isoformat(),
                "entries": entries,
                "raw": proc.stdout[:1000],
            }
        except Exception as e:
            return {"error": str(e), "competition": competition}

    def post_leaderboard_update(
        self,
        forum,
        thread_id: str,
        lb_data: Dict[str, Any],
    ) -> str:
        """Posts a leaderboard update to the forum."""
        entries = lb_data.get("entries", [])
        lines = []
        for i, e in enumerate(entries[:5], 1):
            user_flag = " ← YOU" if e.get("is_user") else ""
            lines.append(f"  {i}. {e.get('teamName', '?')} — {e.get('score', '?')}{user_flag}")
        body = (
            f"📊 **LEADERBOARD UPDATE** — {lb_data.get('competition', '?')}\n\n"
            + ("\n".join(lines) or "  (no data)")
            + f"\n\n*Polled: {lb_data.get('polled_at', '?')[:19]}*"
        )
        return forum.post(self, thread_id, body, metadata={"type": "leaderboard_update"})
