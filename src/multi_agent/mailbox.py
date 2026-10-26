"""
mailbox.py — Agent Mailbox System
===================================
Direct agent-to-agent message passing with persistent inbox.
Chris Deot quote: "sisteme poštanskih sandučića za slanje beleški i datoteka putem poštanskih sandučića"

Features:
- Send/receive text messages between agents
- Attach JSON payloads (file references, kernel results, scores)
- Priority queue (URGENT > HIGH > NORMAL > LOW)
- Read/unread tracking
- CC (carbon copy) to multiple agents

Storage: SQLite research.db table: agent_mailbox
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


class MessagePriority(str, Enum):
    URGENT = "URGENT"
    HIGH   = "HIGH"
    NORMAL = "NORMAL"
    LOW    = "LOW"

    @property
    def sort_order(self) -> int:
        return {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}[self.value]


_DDL = """
CREATE TABLE IF NOT EXISTS agent_mailbox (
    message_id   TEXT PRIMARY KEY,
    from_id      TEXT NOT NULL,
    from_name    TEXT NOT NULL,
    to_id        TEXT NOT NULL,
    to_name      TEXT NOT NULL,
    cc           TEXT DEFAULT '[]',
    subject      TEXT NOT NULL,
    body         TEXT NOT NULL,
    payload      TEXT DEFAULT 'null',
    priority     TEXT DEFAULT 'NORMAL',
    read         INTEGER DEFAULT 0,
    sent_at      TEXT NOT NULL,
    read_at      TEXT,
    thread_id    TEXT,
    in_reply_to  TEXT,
    tags         TEXT DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_mailbox_to   ON agent_mailbox(to_id);
CREATE INDEX IF NOT EXISTS idx_mailbox_from ON agent_mailbox(from_id);
CREATE INDEX IF NOT EXISTS idx_mailbox_read ON agent_mailbox(to_id, read);
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
class Message:
    message_id: str
    from_id: str
    from_name: str
    to_id: str
    to_name: str
    subject: str
    body: str
    sent_at: str
    priority: MessagePriority = MessagePriority.NORMAL
    cc: List[str] = field(default_factory=list)
    payload: Any = None
    read: bool = False
    read_at: Optional[str] = None
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "✓" if self.read else "●"
        ts = self.sent_at[:19].replace("T", " ")
        return f"[{status}][{self.priority.value}] {ts} | From: {self.from_name} | {self.subject}"


class AgentMailbox:
    """
    Agent-to-agent mailbox system.

    Usage:
        mailbox = AgentMailbox()

        # Send a message with a payload (e.g., kernel result)
        mailbox.send(
            sender=manager_agent,
            to_agent_id="engineer_01",
            to_agent_name="Engineer Alpha",
            subject="Kernel Sub-16 completed",
            body="Score: 0.612. Please review logs.",
            payload={"score": 0.612, "kernel_id": "sub16"},
            priority=MessagePriority.HIGH,
        )

        # Read unread inbox
        messages = mailbox.inbox(agent, unread_only=True)
        for msg in messages:
            print(msg)
            mailbox.mark_read(msg.message_id)
    """

    def __init__(self) -> None:
        pass

    def _conn(self) -> sqlite3.Connection:
        return _get_conn()

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send(
        self,
        sender: Any,         # AgentBase
        to_agent_id: str,
        to_agent_name: str,
        subject: str,
        body: str,
        payload: Any = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        cc: Optional[List[str]] = None,
        in_reply_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        _conn: Optional[sqlite3.Connection] = None,
    ) -> str:
        """Sends a message from sender to target agent. Returns message_id. ⚡ Bolt: Supports optional connection reuse."""
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        # Derive thread_id: new thread or inherit from parent
        thread_id = message_id

        conn = _conn or self._conn()
        try:
            if in_reply_to:
                row = conn.execute(
                    "SELECT thread_id FROM agent_mailbox WHERE message_id=?",
                    (in_reply_to,)
                ).fetchone()
                if row and row["thread_id"]:
                    thread_id = row["thread_id"]

            conn.execute("""
                INSERT INTO agent_mailbox
                    (message_id, from_id, from_name, to_id, to_name, cc,
                     subject, body, payload, priority, read, sent_at, thread_id, in_reply_to, tags)
                VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?,?,?)
            """, (
                message_id,
                sender.agent_id, sender.name,
                to_agent_id, to_agent_name,
                json.dumps(cc or []),
                subject, body,
                json.dumps(payload),
                priority.value,
                now,
                thread_id, in_reply_to,
                json.dumps(tags or []),
            ))
            # Also deliver to CC recipients
            for cc_id in (cc or []):
                cc_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
                conn.execute("""
                    INSERT INTO agent_mailbox
                        (message_id, from_id, from_name, to_id, to_name, cc,
                         subject, body, payload, priority, read, sent_at, thread_id, in_reply_to, tags)
                    VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?,?,?)
                """, (
                    cc_msg_id,
                    sender.agent_id, sender.name,
                    cc_id, f"[CC] {cc_id}",
                    json.dumps([]),
                    f"[CC] {subject}", body,
                    json.dumps(payload),
                    MessagePriority.LOW.value,
                    now,
                    thread_id, message_id,
                    json.dumps(tags or []),
                ))
            if _conn is None:
                conn.commit()
        finally:
            if _conn is None:
                conn.close()
        return message_id

    def broadcast(
        self,
        sender: Any,
        agent_ids: List[tuple],   # [(agent_id, agent_name), ...]
        subject: str,
        body: str,
        payload: Any = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        tags: Optional[List[str]] = None,
    ) -> List[str]:
        """Sends the same message to multiple agents within a single transaction. Returns list of message_ids."""
        conn = self._conn()
        try:
            msg_ids = [
                self.send(sender, aid, aname, subject, body, payload, priority, tags=tags, _conn=conn)
                for aid, aname in agent_ids
            ]
            conn.commit()
            return msg_ids
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def inbox(
        self,
        agent: Any,
        unread_only: bool = False,
        limit: int = 50,
        priority: Optional[MessagePriority] = None,
    ) -> List[Message]:
        """Returns messages in agent's inbox, newest first."""
        conn = self._conn()
        clauses = ["to_id = ?"]
        params: list = [agent.agent_id]
        if unread_only:
            clauses.append("read = 0")
        if priority:
            clauses.append("priority = ?")
            params.append(priority.value)
        where = " AND ".join(clauses)
        rows = conn.execute(
            f"SELECT * FROM agent_mailbox WHERE {where} ORDER BY sent_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()
        return [self._row_to_msg(r) for r in rows]

    def sent(self, agent: Any, limit: int = 30) -> List[Message]:
        """Returns messages sent by this agent."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM agent_mailbox WHERE from_id=? ORDER BY sent_at DESC LIMIT ?",
            (agent.agent_id, limit)
        ).fetchall()
        conn.close()
        return [self._row_to_msg(r) for r in rows]

    def thread(self, thread_id: str) -> List[Message]:
        """Returns all messages in a thread, ordered by time."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM agent_mailbox WHERE thread_id=? ORDER BY sent_at ASC",
            (thread_id,)
        ).fetchall()
        conn.close()
        return [self._row_to_msg(r) for r in rows]

    def unread_count(self, agent: Any) -> int:
        """Returns number of unread messages."""
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM agent_mailbox WHERE to_id=? AND read=0",
            (agent.agent_id,)
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0

    # ------------------------------------------------------------------
    # Status management
    # ------------------------------------------------------------------

    def mark_read(self, message_id: str) -> None:
        """Marks a message as read."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute(
            "UPDATE agent_mailbox SET read=1, read_at=? WHERE message_id=?",
            (now, message_id)
        )
        conn.commit()
        conn.close()

    def mark_all_read(self, agent: Any) -> int:
        """Marks all unread messages for an agent as read. Returns count."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        cursor = conn.execute(
            "UPDATE agent_mailbox SET read=1, read_at=? WHERE to_id=? AND read=0",
            (now, agent.agent_id)
        )
        conn.commit()
        count = cursor.rowcount
        conn.close()
        return count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _row_to_msg(self, r: sqlite3.Row) -> Message:
        return Message(
            message_id=r["message_id"],
            from_id=r["from_id"],
            from_name=r["from_name"],
            to_id=r["to_id"],
            to_name=r["to_name"],
            subject=r["subject"],
            body=r["body"],
            sent_at=r["sent_at"],
            priority=MessagePriority(r["priority"]),
            cc=json.loads(r["cc"] or "[]"),
            payload=json.loads(r["payload"]) if r["payload"] and r["payload"] != "null" else None,
            read=bool(r["read"]),
            read_at=r["read_at"],
            thread_id=r["thread_id"],
            in_reply_to=r["in_reply_to"],
            tags=json.loads(r["tags"] or "[]"),
        )

    def print_inbox(self, agent: Any, unread_only: bool = True) -> None:
        """Pretty-prints inbox to stdout."""
        msgs = self.inbox(agent, unread_only=unread_only, limit=20)
        print(f"\n📬 Inbox for {agent.name} ({len(msgs)} messages)")
        print("-" * 60)
        for m in msgs:
            print(f"  {m}")
            if m.payload:
                print(f"    📎 Payload: {json.dumps(m.payload, indent=6)}")
        print("-" * 60)
