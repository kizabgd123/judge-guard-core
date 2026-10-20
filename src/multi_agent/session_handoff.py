"""
session_handoff.py — Asynchronous Session Handoff & Discovery File Protocol
=============================================================================
Implements Chris Deotte's (#1 Kaggle Grandmaster) session handoff protocol:
"сваки агент пише лог и датотеку за откривање након своје N-часовне сесије.
А онда други агенти могу да читају белешке и код од других агената."

Protocol:
1. When an agent completes an experimental session (or N hours), it writes:
   - A structured session log (actions taken, kernels trained, CV/LB scores).
   - A "Discovery File" (`discovery_<session_id>.json` & `.md`) detailing:
     * Empirical findings (what worked, what failed)
     * Invariants / statistical anomalies discovered
     * Generated code / kernel artifacts
     * Concrete recommendations for the NEXT agent
2. When the NEXT agent begins a session, it reads and digests all past discovery
   files to build cumulative intelligence and avoid repeating past dead-ends.

Storage: SQLite research.db table: session_discoveries
Artifact Directory: /home/testovinovi/judge-guard-core-master/exports/discoveries/
Authority: MASTER_ORCHESTRATION.md
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "research.db"
DISCOVERIES_DIR = PROJECT_ROOT / "exports" / "discoveries"


_DDL = """
CREATE TABLE IF NOT EXISTS session_discoveries (
    discovery_id     TEXT PRIMARY KEY,
    competition      TEXT NOT NULL,
    session_id       TEXT NOT NULL,
    author_id        TEXT NOT NULL,
    author_name      TEXT NOT NULL,
    author_role      TEXT NOT NULL,
    duration_minutes REAL DEFAULT 0.0,
    headline         TEXT NOT NULL,
    what_worked      TEXT NOT NULL,
    what_failed      TEXT NOT NULL,
    invariants       TEXT DEFAULT '[]',
    artifacts        TEXT DEFAULT '[]',
    recommendations  TEXT NOT NULL,
    metric_delta     REAL DEFAULT 0.0,
    created_at       TEXT NOT NULL,
    metadata         TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_discoveries_comp ON session_discoveries(competition);
CREATE INDEX IF NOT EXISTS idx_discoveries_time ON session_discoveries(created_at);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    for stmt in _DDL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()
    return conn


@dataclass
class DiscoveryRecord:
    discovery_id: str
    competition: str
    session_id: str
    author_id: str
    author_name: str
    author_role: str
    duration_minutes: float
    headline: str
    what_worked: str
    what_failed: str
    invariants: List[str]
    artifacts: List[str]
    recommendations: str
    metric_delta: float
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        invs = "\n".join(f"- `{inv}`" for inv in self.invariants) or "None recorded"
        arts = "\n".join(f"- `{art}`" for art in self.artifacts) or "None recorded"
        return f"""# 🔭 DISCOVERY FILE: {self.headline}

**Session ID:** `{self.session_id}`
**Author:** {self.author_name} ({self.author_role})
**Competition:** `{self.competition}`
**Duration:** {self.duration_minutes:.1f} minutes
**Metric Delta:** {self.metric_delta:+.4f}
**Date:** {self.created_at}

---

### 💡 What Worked
{self.what_worked}

### 🛑 What Failed (Dead Ends to Avoid)
{self.what_failed}

### 🔍 Invariants Discovered
{invs}

### 📦 Artifacts & Code Generated
{arts}

### 🎯 Recommendations for the Next Agent
{self.recommendations}
"""


class SessionHandoffManager:
    """
    Manages the lifecycle of agent session handoffs and discovery files.
    """

    def __init__(self, competition: str = "general") -> None:
        self.competition = competition
        DISCOVERIES_DIR.mkdir(parents=True, exist_ok=True)

    def _conn(self) -> sqlite3.Connection:
        return _get_conn()

    def record_discovery(
        self,
        agent: Any,
        session_id: str,
        headline: str,
        what_worked: str,
        what_failed: str,
        recommendations: str,
        invariants: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        duration_minutes: float = 60.0,
        metric_delta: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DiscoveryRecord:
        """
        Records a discovery file in SQLite and writes markdown to disk.
        Returns the created DiscoveryRecord.
        """
        discovery_id = f"disc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        invariants = invariants or []
        artifacts = artifacts or []
        metadata = metadata or {}
        role_val = agent.role.value if hasattr(agent, "role") else "unknown"

        record = DiscoveryRecord(
            discovery_id=discovery_id,
            competition=self.competition,
            session_id=session_id,
            author_id=agent.agent_id,
            author_name=agent.name,
            author_role=role_val,
            duration_minutes=duration_minutes,
            headline=headline,
            what_worked=what_worked,
            what_failed=what_failed,
            invariants=invariants,
            artifacts=artifacts,
            recommendations=recommendations,
            metric_delta=metric_delta,
            created_at=now,
            metadata=metadata,
        )

        # 1. Persist to SQLite
        conn = self._conn()
        conn.execute("""
            INSERT INTO session_discoveries (
                discovery_id, competition, session_id, author_id, author_name, author_role,
                duration_minutes, headline, what_worked, what_failed, invariants, artifacts,
                recommendations, metric_delta, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            discovery_id, self.competition, session_id,
            agent.agent_id, agent.name, role_val,
            duration_minutes, headline, what_worked, what_failed,
            json.dumps(invariants), json.dumps(artifacts),
            recommendations, metric_delta, now,
            json.dumps(metadata)
        ))
        conn.commit()
        conn.close()

        # 2. Write Markdown to export directory
        md_path = DISCOVERIES_DIR / f"{self.competition}_{session_id}_{discovery_id}.md"
        md_path.write_text(record.to_markdown(), encoding="utf-8")

        # 3. Write JSON artifact
        json_path = DISCOVERIES_DIR / f"{self.competition}_{session_id}_{discovery_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "discovery_id": discovery_id,
                "competition": self.competition,
                "session_id": session_id,
                "author": {"id": agent.agent_id, "name": agent.name, "role": role_val},
                "headline": headline,
                "metric_delta": metric_delta,
                "what_worked": what_worked,
                "what_failed": what_failed,
                "invariants": invariants,
                "artifacts": artifacts,
                "recommendations": recommendations,
                "created_at": now
            }, f, indent=2)

        return record

    def read_past_discoveries(self, limit: int = 10) -> List[DiscoveryRecord]:
        """
        Retrieves past discoveries for this competition, newest first.
        Allows the starting agent to ingest cumulative knowledge.
        """
        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM session_discoveries
            WHERE competition = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (self.competition, limit)).fetchall()
        conn.close()

        records = []
        for r in rows:
            records.append(DiscoveryRecord(
                discovery_id=r["discovery_id"],
                competition=r["competition"],
                session_id=r["session_id"],
                author_id=r["author_id"],
                author_name=r["author_name"],
                author_role=r["author_role"],
                duration_minutes=r["duration_minutes"],
                headline=r["headline"],
                what_worked=r["what_worked"],
                what_failed=r["what_failed"],
                invariants=json.loads(r["invariants"] or "[]"),
                artifacts=json.loads(r["artifacts"] or "[]"),
                recommendations=r["recommendations"],
                metric_delta=r["metric_delta"],
                created_at=r["created_at"],
                metadata=json.loads(r["metadata"] or "{}"),
            ))
        return records

    def build_cumulative_briefing(self, next_agent: Any, limit: int = 5) -> str:
        """
        Builds a comprehensive markdown briefing of all past discoveries
        specifically for the incoming agent.
        """
        past = self.read_past_discoveries(limit=limit)
        if not past:
            return f"Welcome {next_agent.name}! No previous discovery files found for {self.competition}. You are pioneer Agent #1."

        briefing = [
            f"# 📜 CUMULATIVE AGENT KNOWLEDGE BRIEFING: {self.competition.upper()}",
            f"**Prepared for:** {next_agent.name} [{getattr(next_agent, 'role', '')}]",
            f"**Total Past Sessions Ingested:** {len(past)}\n",
            "## 🧠 Synthesized Findings Across Sessions:\n"
        ]

        for i, d in enumerate(past, 1):
            briefing.append(f"### Session #{i}: {d.headline} (by {d.author_name})")
            briefing.append(f"- **Outcome:** Metric Delta: {d.metric_delta:+.4f}")
            briefing.append(f"- **Validated:** {d.what_worked[:250]}...")
            briefing.append(f"- **Avoid:** {d.what_failed[:250]}...")
            if d.invariants:
                briefing.append(f"- **Invariants:** {', '.join(d.invariants)}")
            briefing.append(f"- **Direct Instruction for You:** {d.recommendations}\n")

        return "\n".join(briefing)
