"""
hierarchy.py — Manager-Employee Agent Hierarchy
=================================================
Implements the task delegation tree described by Chris Deot:
"oркестрирао сам сложене хијерархије управљања где запослени примају наређења од менаџера"

Features:
- Define manager → employee relationships
- Manager issues Tasks to employees
- Employees accept, work, and report back
- Task status tracking (PENDING → ACCEPTED → IN_PROGRESS → DONE / FAILED)
- Manager can reassign or escalate tasks

Storage: SQLite research.db tables: agent_hierarchy, agent_tasks
Authority: MASTER_ORCHESTRATION.md
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "research.db"


class TaskStatus(str, Enum):
    PENDING     = "PENDING"
    ACCEPTED    = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE        = "DONE"
    FAILED      = "FAILED"
    ESCALATED   = "ESCALATED"


_DDL = """
CREATE TABLE IF NOT EXISTS agent_hierarchy (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    manager_id      TEXT NOT NULL,
    manager_name    TEXT NOT NULL,
    employee_id     TEXT NOT NULL,
    employee_name   TEXT NOT NULL,
    team_name       TEXT DEFAULT 'default',
    created_at      TEXT NOT NULL,
    UNIQUE(manager_id, employee_id, team_name)
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    task_id         TEXT PRIMARY KEY,
    team_name       TEXT DEFAULT 'default',
    issued_by       TEXT NOT NULL,
    issued_by_name  TEXT NOT NULL,
    assigned_to     TEXT NOT NULL,
    assigned_to_name TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    status          TEXT DEFAULT 'PENDING',
    priority        INTEGER DEFAULT 5,
    created_at      TEXT NOT NULL,
    accepted_at     TEXT,
    started_at      TEXT,
    completed_at    TEXT,
    result          TEXT DEFAULT 'null',
    notes           TEXT DEFAULT '',
    deadline        TEXT,
    depends_on      TEXT DEFAULT '[]',
    metadata        TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON agent_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status   ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_team     ON agent_tasks(team_name);
"""


_db_initialized = False
_db_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    global _db_initialized
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    if not _db_initialized:
        with _db_lock:
            if not _db_initialized:
                for stmt in _DDL.strip().split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        conn.execute(stmt)
                conn.commit()
                _db_initialized = True
    return conn


@dataclass
class Task:
    task_id: str
    team_name: str
    issued_by: str
    issued_by_name: str
    assigned_to: str
    assigned_to_name: str
    title: str
    description: str
    status: TaskStatus
    priority: int
    created_at: str
    accepted_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Any = None
    notes: str = ""
    deadline: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_done(self) -> bool:
        return self.status in (TaskStatus.DONE, TaskStatus.FAILED)

    def __str__(self) -> str:
        icon = {
            "PENDING": "⏳", "ACCEPTED": "🤝", "IN_PROGRESS": "🔄",
            "DONE": "✅", "FAILED": "❌", "ESCALATED": "🚨"
        }.get(self.status.value, "?")
        return f"{icon} [{self.priority}] {self.title} → {self.assigned_to_name} ({self.status.value})"


class AgentHierarchy:
    """
    Manager-Employee task delegation system.

    Usage:
        hierarchy = AgentHierarchy(team_name="ntl_team")
        hierarchy.register_employee(manager, engineer_agent)
        hierarchy.register_employee(manager, researcher_agent)

        task_id = hierarchy.assign_task(
            manager,
            to_agent=engineer_agent,
            title="Build Sub-17 Kernel",
            description="Implement dual-trunk LoRA with WPCA heads...",
            priority=1,
        )

        hierarchy.accept_task(engineer_agent, task_id)
        hierarchy.start_task(engineer_agent, task_id)
        hierarchy.complete_task(engineer_agent, task_id, result={"score": 0.615})

        # Manager view
        tasks = hierarchy.my_assigned_tasks(manager)
        report = hierarchy.team_status_report(manager)
    """

    def __init__(self, team_name: str = "default") -> None:
        self.team_name = team_name

    def _conn(self) -> sqlite3.Connection:
        return _get_conn()

    # ------------------------------------------------------------------
    # Hierarchy registration
    # ------------------------------------------------------------------

    def register_employee(self, manager: Any, employee: Any) -> None:
        """Registers manager → employee relationship."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            INSERT OR IGNORE INTO agent_hierarchy
                (manager_id, manager_name, employee_id, employee_name, team_name, created_at)
            VALUES (?,?,?,?,?,?)
        """, (
            manager.agent_id, manager.name,
            employee.agent_id, employee.name,
            self.team_name, now,
        ))
        conn.commit()
        conn.close()

    def get_employees(self, manager: Any) -> List[Dict[str, str]]:
        """Returns list of employees under this manager."""
        conn = self._conn()
        rows = conn.execute("""
            SELECT employee_id, employee_name FROM agent_hierarchy
            WHERE manager_id=? AND team_name=?
        """, (manager.agent_id, self.team_name)).fetchall()
        conn.close()
        return [{"agent_id": r["employee_id"], "name": r["employee_name"]} for r in rows]

    def get_manager(self, employee: Any) -> Optional[Dict[str, str]]:
        """Returns the manager of this employee (if any)."""
        conn = self._conn()
        row = conn.execute("""
            SELECT manager_id, manager_name FROM agent_hierarchy
            WHERE employee_id=? AND team_name=?
        """, (employee.agent_id, self.team_name)).fetchone()
        conn.close()
        return {"agent_id": row["manager_id"], "name": row["manager_name"]} if row else None

    # ------------------------------------------------------------------
    # Task issuance
    # ------------------------------------------------------------------

    def assign_task(
        self,
        issuer: Any,
        to_agent: Any,
        title: str,
        description: str,
        priority: int = 5,
        deadline: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Assigns a task from issuer to employee. Returns task_id."""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            INSERT INTO agent_tasks
                (task_id, team_name, issued_by, issued_by_name, assigned_to, assigned_to_name,
                 title, description, status, priority, created_at, deadline, depends_on, metadata)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            task_id, self.team_name,
            issuer.agent_id, issuer.name,
            to_agent.agent_id, to_agent.name,
            title, description,
            TaskStatus.PENDING.value, priority, now,
            deadline,
            json.dumps(depends_on or []),
            json.dumps(metadata or {}),
        ))
        conn.commit()
        conn.close()
        return task_id

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------

    def accept_task(self, agent: Any, task_id: str) -> None:
        """Employee accepts a task."""
        self._transition(task_id, TaskStatus.ACCEPTED, agent,
                         "accepted_at", TaskStatus.PENDING)

    def start_task(self, agent: Any, task_id: str) -> None:
        """Employee starts working on a task."""
        self._transition(task_id, TaskStatus.IN_PROGRESS, agent,
                         "started_at", TaskStatus.ACCEPTED)

    def complete_task(self, agent: Any, task_id: str, result: Any = None, notes: str = "") -> None:
        """Employee marks task as complete with optional result payload."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            UPDATE agent_tasks
            SET status=?, completed_at=?, result=?, notes=?
            WHERE task_id=? AND assigned_to=?
        """, (
            TaskStatus.DONE.value, now,
            json.dumps(result), notes,
            task_id, agent.agent_id,
        ))
        conn.commit()
        conn.close()

    def fail_task(self, agent: Any, task_id: str, reason: str = "") -> None:
        """Employee marks task as failed."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            UPDATE agent_tasks SET status=?, completed_at=?, notes=?
            WHERE task_id=? AND assigned_to=?
        """, (TaskStatus.FAILED.value, now, reason, task_id, agent.agent_id))
        conn.commit()
        conn.close()

    def escalate_task(self, agent: Any, task_id: str, reason: str = "") -> None:
        """Employee escalates a blocked task back to manager."""
        conn = self._conn()
        conn.execute("""
            UPDATE agent_tasks SET status=?, notes=?
            WHERE task_id=?
        """, (TaskStatus.ESCALATED.value, reason, task_id))
        conn.commit()
        conn.close()

    def _transition(
        self, task_id: str, new_status: TaskStatus,
        agent: Any, timestamp_field: str, expected_status: TaskStatus
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute(f"""
            UPDATE agent_tasks
            SET status=?, {timestamp_field}=?
            WHERE task_id=? AND assigned_to=? AND status=?
        """, (new_status.value, now, task_id, agent.agent_id, expected_status.value))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def my_tasks(self, agent: Any, status: Optional[TaskStatus] = None) -> List[Task]:
        """Returns tasks assigned TO this agent."""
        return self._query_tasks("assigned_to", agent.agent_id, status)

    def my_assigned_tasks(self, manager: Any, status: Optional[TaskStatus] = None) -> List[Task]:
        """Returns tasks issued BY this manager."""
        return self._query_tasks("issued_by", manager.agent_id, status)

    def _query_tasks(self, field: str, agent_id: str, status: Optional[TaskStatus]) -> List[Task]:
        conn = self._conn()
        if status:
            rows = conn.execute(
                f"SELECT * FROM agent_tasks WHERE {field}=? AND status=? AND team_name=? ORDER BY priority ASC",
                (agent_id, status.value, self.team_name)
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM agent_tasks WHERE {field}=? AND team_name=? ORDER BY priority ASC",
                (agent_id, self.team_name)
            ).fetchall()
        conn.close()
        return [self._row_to_task(r) for r in rows]

    def team_status_report(self, manager: Any) -> Dict[str, Any]:
        """Returns a summary report of team task status."""
        tasks = self.my_assigned_tasks(manager)
        by_status: Dict[str, List[str]] = {}
        for t in tasks:
            by_status.setdefault(t.status.value, []).append(t.title)
        return {
            "team": self.team_name,
            "manager": manager.name,
            "total_tasks": len(tasks),
            "by_status": by_status,
            "employees": self.get_employees(manager),
        }

    def print_report(self, manager: Any) -> None:
        """Pretty-prints team status report."""
        report = self.team_status_report(manager)
        print(f"\n{'='*60}")
        print(f"👔 Team: {report['team']}  Manager: {report['manager']}")
        print(f"{'='*60}")
        for status, titles in report["by_status"].items():
            icon = {"PENDING": "⏳", "ACCEPTED": "🤝", "IN_PROGRESS": "🔄",
                    "DONE": "✅", "FAILED": "❌", "ESCALATED": "🚨"}.get(status, "?")
            print(f"  {icon} {status}: {len(titles)}")
            for t in titles:
                print(f"       - {t}")
        print(f"\n  👥 Employees: {[e['name'] for e in report['employees']]}")
        print(f"{'='*60}\n")

    def _row_to_task(self, r: sqlite3.Row) -> Task:
        return Task(
            task_id=r["task_id"],
            team_name=r["team_name"],
            issued_by=r["issued_by"],
            issued_by_name=r["issued_by_name"],
            assigned_to=r["assigned_to"],
            assigned_to_name=r["assigned_to_name"],
            title=r["title"],
            description=r["description"],
            status=TaskStatus(r["status"]),
            priority=r["priority"],
            created_at=r["created_at"],
            accepted_at=r["accepted_at"],
            started_at=r["started_at"],
            completed_at=r["completed_at"],
            result=json.loads(r["result"]) if r["result"] and r["result"] != "null" else None,
            notes=r["notes"] or "",
            deadline=r["deadline"],
            depends_on=json.loads(r["depends_on"] or "[]"),
            metadata=json.loads(r["metadata"] or "{}"),
        )
