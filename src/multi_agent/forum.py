"""
forum.py — Agent Forum System
==============================
Multi-agent discussion board (like the Kaggle forum, but for agents).
Agents can post, reply, react, and read threads.
Chris Deot quote: "forume, slične Kaggle forumu gdje više agenta ćaska jedni sa drugima"

Storage: SQLite research.db tables: forum_threads, forum_posts
Authority: MASTER_ORCHESTRATION.md
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "research.db"

VALID_REACTIONS = {"👍", "👎", "🔥", "💡", "❓", "✅", "🛑"}


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS forum_threads (
    thread_id   TEXT PRIMARY KEY,
    forum_name  TEXT NOT NULL DEFAULT 'general',
    title       TEXT NOT NULL,
    author_id   TEXT NOT NULL,
    author_name TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    pinned      INTEGER DEFAULT 0,
    tags        TEXT DEFAULT '[]',
    metadata    TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS forum_posts (
    post_id     TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL REFERENCES forum_threads(thread_id),
    parent_id   TEXT,
    author_id   TEXT NOT NULL,
    author_name TEXT NOT NULL,
    body        TEXT NOT NULL,
    reactions   TEXT DEFAULT '{}',
    created_at  TEXT NOT NULL,
    edited_at   TEXT,
    metadata    TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_forum_posts_thread ON forum_posts(thread_id);
CREATE INDEX IF NOT EXISTS idx_forum_posts_created ON forum_posts(created_at);
"""


_db_initialized = False
_db_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    global _db_initialized
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
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


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ForumThread:
    thread_id: str
    forum_name: str
    title: str
    author_id: str
    author_name: str
    created_at: str
    pinned: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    post_count: int = 0


@dataclass
class ForumPost:
    post_id: str
    thread_id: str
    author_id: str
    author_name: str
    body: str
    created_at: str
    parent_id: Optional[str] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> [agent_ids]
    edited_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# AgentForum
# ---------------------------------------------------------------------------

class AgentForum:
    """
    Multi-agent forum.

    Usage:
        forum = AgentForum("name_that_llm")
        thread_id = forum.create_thread(agent, "Round 12 — What's our next experiment?")
        post_id   = forum.post(agent, thread_id, "I think we should try curly-quote invariants...")
        forum.reply(agent, thread_id, post_id, "Agree! LLaMA also benefits from em-dash guard.")
        forum.react(agent, post_id, "🔥")
        threads = forum.list_threads()
        posts   = forum.read_thread(thread_id)
    """

    def __init__(self, forum_name: str = "general") -> None:
        self.forum_name = forum_name

    def _conn(self) -> sqlite3.Connection:
        return _get_conn()

    # ------------------------------------------------------------------
    # Thread management
    # ------------------------------------------------------------------

    def create_thread(
        self,
        agent: Any,  # AgentBase
        title: str,
        tags: Optional[List[str]] = None,
        pinned: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Creates a new discussion thread. Returns thread_id."""
        import uuid
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            INSERT INTO forum_threads
                (thread_id, forum_name, title, author_id, author_name, created_at, pinned, tags, metadata)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            thread_id, self.forum_name, title,
            agent.agent_id, agent.name, now,
            int(pinned),
            json.dumps(tags or []),
            json.dumps(metadata or {}),
        ))
        conn.commit()
        conn.close()
        return thread_id

    def list_threads(
        self,
        limit: int = 20,
        tags: Optional[List[str]] = None,
    ) -> List[ForumThread]:
        """Lists threads in this forum, newest first."""
        conn = self._conn()
        # ⚡ Bolt: Push tag filtering down into SQLite using json_each(t.tags)
        # BEFORE GROUP BY and LIMIT. This avoids fetching and deserializing
        # unneeded non-matching rows in Python and prevents result truncation
        # when matching threads occur further down in the table.
        if tags:
            tag_placeholders = ",".join("?" for _ in tags)
            query = f"""
                SELECT t.*, COUNT(p.post_id) AS post_count
                FROM forum_threads t
                LEFT JOIN forum_posts p ON p.thread_id = t.thread_id
                WHERE t.forum_name = ?
                  AND EXISTS (
                      SELECT 1 FROM json_each(t.tags) WHERE value IN ({tag_placeholders})
                  )
                GROUP BY t.thread_id
                ORDER BY t.pinned DESC, t.created_at DESC
                LIMIT ?
            """
            params = [self.forum_name] + list(tags) + [limit]
        else:
            query = """
                SELECT t.*, COUNT(p.post_id) AS post_count
                FROM forum_threads t
                LEFT JOIN forum_posts p ON p.thread_id = t.thread_id
                WHERE t.forum_name = ?
                GROUP BY t.thread_id
                ORDER BY t.pinned DESC, t.created_at DESC
                LIMIT ?
            """
            params = [self.forum_name, limit]

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [
            ForumThread(
                thread_id=r["thread_id"],
                forum_name=r["forum_name"],
                title=r["title"],
                author_id=r["author_id"],
                author_name=r["author_name"],
                created_at=r["created_at"],
                pinned=bool(r["pinned"]),
                tags=json.loads(r["tags"] or "[]"),
                metadata=json.loads(r["metadata"] or "{}"),
                post_count=r["post_count"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Posting
    # ------------------------------------------------------------------

    def post(
        self,
        agent: Any,
        thread_id: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Posts a top-level message in a thread. Returns post_id."""
        return self._insert_post(agent, thread_id, body, None, metadata)

    def reply(
        self,
        agent: Any,
        thread_id: str,
        parent_post_id: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Replies to a specific post in a thread. Returns post_id."""
        return self._insert_post(agent, thread_id, body, parent_post_id, metadata)

    def _insert_post(
        self,
        agent: Any,
        thread_id: str,
        body: str,
        parent_id: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        import uuid
        post_id = f"post_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            INSERT INTO forum_posts
                (post_id, thread_id, parent_id, author_id, author_name, body, reactions, created_at, metadata)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            post_id, thread_id, parent_id,
            agent.agent_id, agent.name, body,
            json.dumps({}), now,
            json.dumps(metadata or {}),
        ))
        conn.commit()
        conn.close()
        return post_id

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def read_thread(
        self,
        thread_id: str,
        limit: int = 100,
    ) -> List[ForumPost]:
        """Reads all posts in a thread, oldest first."""
        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM forum_posts
            WHERE thread_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (thread_id, limit)).fetchall()
        conn.close()
        return [
            ForumPost(
                post_id=r["post_id"],
                thread_id=r["thread_id"],
                author_id=r["author_id"],
                author_name=r["author_name"],
                body=r["body"],
                created_at=r["created_at"],
                parent_id=r["parent_id"],
                reactions=json.loads(r["reactions"] or "{}"),
                edited_at=r["edited_at"],
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    def read_latest(self, limit: int = 10) -> List[ForumPost]:
        """Reads the latest posts across all threads in this forum."""
        conn = self._conn()
        rows = conn.execute("""
            SELECT p.* FROM forum_posts p
            JOIN forum_threads t ON t.thread_id = p.thread_id
            WHERE t.forum_name = ?
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (self.forum_name, limit)).fetchall()
        conn.close()
        return [
            ForumPost(
                post_id=r["post_id"],
                thread_id=r["thread_id"],
                author_id=r["author_id"],
                author_name=r["author_name"],
                body=r["body"],
                created_at=r["created_at"],
                parent_id=r["parent_id"],
                reactions=json.loads(r["reactions"] or "{}"),
                edited_at=r["edited_at"],
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Reactions
    # ------------------------------------------------------------------

    def react(self, agent: Any, post_id: str, emoji: str) -> None:
        """Adds or toggles a reaction on a post."""
        if emoji not in VALID_REACTIONS:
            raise ValueError(f"Invalid reaction '{emoji}'. Valid: {VALID_REACTIONS}")
        conn = self._conn()
        row = conn.execute(
            "SELECT reactions FROM forum_posts WHERE post_id=?", (post_id,)
        ).fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Post {post_id} not found")
        reactions: Dict[str, List[str]] = json.loads(row["reactions"] or "{}")
        agent_list = reactions.get(emoji, [])
        if agent.agent_id in agent_list:
            agent_list.remove(agent.agent_id)  # toggle off
        else:
            agent_list.append(agent.agent_id)
        reactions[emoji] = agent_list
        conn.execute(
            "UPDATE forum_posts SET reactions=? WHERE post_id=?",
            (json.dumps(reactions), post_id)
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def print_thread(self, thread_id: str) -> None:
        """Pretty-prints a thread to stdout (for CLI debugging)."""
        posts = self.read_thread(thread_id)
        print(f"\n{'='*60}")
        print(f"📋 Thread: {thread_id}  [{self.forum_name}]")
        print(f"{'='*60}")
        for p in posts:
            indent = "  ↳ " if p.parent_id else ""
            ts = p.created_at[:19].replace("T", " ")
            rxn = "  " + " ".join(
                f"{emoji}×{len(ids)}" for emoji, ids in p.reactions.items() if ids
            ) if any(p.reactions.values()) else ""
            print(f"{indent}[{ts}] {p.author_name}: {p.body}{rxn}")
        print(f"{'='*60}\n")
