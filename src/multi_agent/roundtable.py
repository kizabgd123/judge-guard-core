"""
roundtable.py — Round-Table Voting System
==========================================
Consensus-driven experiment selection via agent voting.
Chris Deot quote: "сложену сарадњу округлог стола где сви агенти подносе
и разговарају о идејама, а гласа се о следећем експерименту"

Protocol:
1. Any agent can PROPOSE an experiment
2. All agents receive notification and can DISCUSS (via forum or mailbox)
3. VOTE phase: each agent submits a vote (YES/NO/ABSTAIN + weight)
   - Manager votes count DOUBLE (per Chris Deot hierarchy rules)
4. RESULT: winning proposal is committed; loser proposals get archived
5. EXECUTE: the winning experiment is queued for kernel submission

Storage: SQLite research.db tables: roundtable_sessions, roundtable_proposals, roundtable_votes
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
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "research.db"


class VoteChoice(str, Enum):
    YES     = "YES"
    NO      = "NO"
    ABSTAIN = "ABSTAIN"


class SessionStatus(str, Enum):
    OPEN      = "OPEN"       # accepting proposals + votes
    VOTING    = "VOTING"     # vote phase, no new proposals
    CLOSED    = "CLOSED"     # winner declared
    CANCELLED = "CANCELLED"


class ProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    WINNER   = "WINNER"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


_DDL = """
CREATE TABLE IF NOT EXISTS roundtable_sessions (
    session_id   TEXT PRIMARY KEY,
    competition  TEXT NOT NULL,
    topic        TEXT NOT NULL,
    status       TEXT DEFAULT 'OPEN',
    created_by   TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    voting_ends  TEXT,
    winner_id    TEXT,
    metadata     TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS roundtable_proposals (
    proposal_id  TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL REFERENCES roundtable_sessions(session_id),
    author_id    TEXT NOT NULL,
    author_name  TEXT NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    experiment   TEXT DEFAULT '{}',
    status       TEXT DEFAULT 'PROPOSED',
    score_target REAL,
    created_at   TEXT NOT NULL,
    metadata     TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS roundtable_votes (
    vote_id      TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    proposal_id  TEXT NOT NULL,
    voter_id     TEXT NOT NULL,
    voter_name   TEXT NOT NULL,
    voter_role   TEXT NOT NULL,
    choice       TEXT NOT NULL,
    weight       REAL DEFAULT 1.0,
    rationale    TEXT DEFAULT '',
    voted_at     TEXT NOT NULL,
    UNIQUE(session_id, proposal_id, voter_id)
);

CREATE INDEX IF NOT EXISTS idx_proposals_session ON roundtable_proposals(session_id);
CREATE INDEX IF NOT EXISTS idx_votes_session     ON roundtable_votes(session_id);
CREATE INDEX IF NOT EXISTS idx_votes_proposal    ON roundtable_votes(proposal_id);
"""


_db_lock = threading.Lock()
_db_initialized = False


def _get_conn() -> sqlite3.Connection:
    global _db_initialized
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    # ⚡ Bolt: Execute DDL once per process lifecycle to prevent redundant SQL splits & execution
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
class Proposal:
    proposal_id: str
    session_id: str
    author_id: str
    author_name: str
    title: str
    description: str
    experiment: Dict[str, Any]
    status: ProposalStatus
    created_at: str
    score_target: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    yes_weight: float = 0.0
    no_weight: float = 0.0
    abstain_weight: float = 0.0

    @property
    def net_score(self) -> float:
        return self.yes_weight - self.no_weight

    def __str__(self) -> str:
        icon = {"PROPOSED": "💡", "WINNER": "🏆", "REJECTED": "❌", "ARCHIVED": "📦"}.get(
            self.status.value, "?"
        )
        target = f" → target {self.score_target:.4f}" if self.score_target else ""
        return f"{icon} [{self.proposal_id[-6:]}] {self.title}{target} | Score: +{self.yes_weight:.1f}/-{self.no_weight:.1f}"


@dataclass
class Vote:
    vote_id: str
    session_id: str
    proposal_id: str
    voter_id: str
    voter_name: str
    voter_role: str
    choice: VoteChoice
    weight: float
    rationale: str
    voted_at: str


@dataclass
class VotingResult:
    session_id: str
    winner: Optional[Proposal]
    all_proposals: List[Proposal]
    total_votes: int
    participation: float  # 0.0 – 1.0

    def __str__(self) -> str:
        if self.winner:
            return (
                f"🏆 WINNER: {self.winner.title}\n"
                f"   Net score: {self.winner.net_score:+.1f} "
                f"(YES {self.winner.yes_weight:.1f} / NO {self.winner.no_weight:.1f})\n"
                f"   Participation: {self.participation:.0%} ({self.total_votes} votes)"
            )
        return "❌ No winner — tie or all ABSTAIN"


# ---------------------------------------------------------------------------
# RoundTable
# ---------------------------------------------------------------------------

class RoundTable:
    """
    Round-table voting for Kaggle experiment selection.

    Usage:
        rt = RoundTable(competition="name_that_llm")

        # Create a session
        session_id = rt.create_session(manager_agent, topic="Which experiment next?")

        # Agents propose ideas
        p1 = rt.propose(researcher, session_id, "Curly-Quote Invariant", "...", experiment={...}, score_target=0.620)
        p2 = rt.propose(engineer, session_id, "Em-Dash + LoRA Duo", "...", experiment={...}, score_target=0.615)

        # All agents vote (manager double-weighted)
        rt.vote(manager, session_id, p1, VoteChoice.YES, rationale="High confidence signal")
        rt.vote(engineer, session_id, p2, VoteChoice.YES)
        rt.vote(researcher, session_id, p1, VoteChoice.YES)

        # Close voting and get winner
        result = rt.close_and_tally(manager, session_id)
        print(result)
    """

    # Manager role weight multiplier (double vote per Chris Deot hierarchy)
    MANAGER_WEIGHT = 2.0
    DEFAULT_WEIGHT = 1.0

    def __init__(self, competition: str = "general") -> None:
        self.competition = competition

    def _conn(self) -> sqlite3.Connection:
        return _get_conn()

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def create_session(
        self,
        creator: Any,
        topic: str,
        voting_ends: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Creates a new round-table session. Returns session_id."""
        session_id = f"rt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            INSERT INTO roundtable_sessions
                (session_id, competition, topic, status, created_by, created_at, voting_ends, metadata)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            session_id, self.competition, topic,
            SessionStatus.OPEN.value,
            creator.agent_id, now,
            voting_ends, json.dumps(metadata or {}),
        ))
        conn.commit()
        conn.close()
        return session_id

    def open_voting(self, session_id: str) -> None:
        """Transitions session from OPEN (proposal phase) to VOTING phase."""
        conn = self._conn()
        conn.execute(
            "UPDATE roundtable_sessions SET status=? WHERE session_id=? AND status=?",
            (SessionStatus.VOTING.value, session_id, SessionStatus.OPEN.value)
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Proposals
    # ------------------------------------------------------------------

    def propose(
        self,
        agent: Any,
        session_id: str,
        title: str,
        description: str,
        experiment: Optional[Dict[str, Any]] = None,
        score_target: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submits a proposal. Returns proposal_id."""
        proposal_id = f"prop_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute("""
            INSERT INTO roundtable_proposals
                (proposal_id, session_id, author_id, author_name, title, description,
                 experiment, status, score_target, created_at, metadata)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            proposal_id, session_id,
            agent.agent_id, agent.name,
            title, description,
            json.dumps(experiment or {}),
            ProposalStatus.PROPOSED.value,
            score_target, now,
            json.dumps(metadata or {}),
        ))
        conn.commit()
        conn.close()
        return proposal_id

    def list_proposals(self, session_id: str) -> List[Proposal]:
        """Lists all proposals for a session."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM roundtable_proposals WHERE session_id=? ORDER BY created_at ASC",
            (session_id,)
        ).fetchall()
        conn.close()
        proposals = [self._row_to_proposal(r) for r in rows]
        return self._attach_vote_tallies(proposals, session_id)

    # ------------------------------------------------------------------
    # Voting
    # ------------------------------------------------------------------

    def vote(
        self,
        agent: Any,
        session_id: str,
        proposal_id: str,
        choice: VoteChoice,
        rationale: str = "",
    ) -> str:
        """Casts or updates a vote. Returns vote_id."""
        # Determine weight based on role
        weight = self.MANAGER_WEIGHT if getattr(agent, "role", None) and \
                 agent.role.value == "manager" else self.DEFAULT_WEIGHT
        vote_id = f"vote_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        role_val = agent.role.value if hasattr(agent, "role") else "unknown"
        conn = self._conn()
        conn.execute("""
            INSERT INTO roundtable_votes
                (vote_id, session_id, proposal_id, voter_id, voter_name, voter_role,
                 choice, weight, rationale, voted_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(session_id, proposal_id, voter_id) DO UPDATE SET
                choice=excluded.choice,
                weight=excluded.weight,
                rationale=excluded.rationale,
                voted_at=excluded.voted_at
        """, (
            vote_id, session_id, proposal_id,
            agent.agent_id, agent.name, role_val,
            choice.value, weight, rationale, now,
        ))
        conn.commit()
        conn.close()
        return vote_id

    def tally(self, session_id: str) -> VotingResult:
        """Tallies votes for all proposals. Does NOT close the session."""
        proposals = self.list_proposals(session_id)
        if not proposals:
            return VotingResult(session_id, None, [], 0, 0.0)

        winner = max(proposals, key=lambda p: p.net_score)
        if winner.net_score <= 0:
            winner = None

        conn = self._conn()
        total_votes = conn.execute(
            "SELECT COUNT(DISTINCT voter_id) as cnt FROM roundtable_votes WHERE session_id=?",
            (session_id,)
        ).fetchone()["cnt"]
        conn.close()

        # Participation = voters / proposals (rough measure)
        participation = min(1.0, total_votes / max(1, len(proposals)))
        return VotingResult(
            session_id=session_id,
            winner=winner,
            all_proposals=sorted(proposals, key=lambda p: p.net_score, reverse=True),
            total_votes=total_votes,
            participation=participation,
        )

    def close_and_tally(self, closer: Any, session_id: str) -> VotingResult:
        """Closes session and declares winner. Marks proposal statuses."""
        result = self.tally(session_id)
        conn = self._conn()
        # Mark winner and rejected proposals
        for p in result.all_proposals:
            if result.winner and p.proposal_id == result.winner.proposal_id:
                status = ProposalStatus.WINNER
            else:
                status = ProposalStatus.REJECTED
            p.status = status
            conn.execute(
                "UPDATE roundtable_proposals SET status=? WHERE proposal_id=?",
                (status.value, p.proposal_id)
            )
        if result.winner:
            result.winner.status = ProposalStatus.WINNER
        # Update session status and winner_id
        winner_id = result.winner.proposal_id if result.winner else None
        conn.execute("""
            UPDATE roundtable_sessions
            SET status=?, winner_id=?
            WHERE session_id=?
        """, (SessionStatus.CLOSED.value, winner_id, session_id))
        conn.commit()
        conn.close()
        return result

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def print_session(self, session_id: str) -> None:
        """Pretty-prints session state."""
        conn = self._conn()
        session = conn.execute(
            "SELECT * FROM roundtable_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        conn.close()
        if not session:
            print("Session not found")
            return
        proposals = self.list_proposals(session_id)
        print(f"\n{'='*65}")
        print(f"🔵 Round-Table | {session['competition']} | {session['status']}")
        print(f"   Topic: {session['topic']}")
        print(f"{'='*65}")
        for p in sorted(proposals, key=lambda x: x.net_score, reverse=True):
            print(f"  {p}")
        result = self.tally(session_id)
        print(f"\n  👥 Votes cast: {result.total_votes}")
        if result.winner:
            print(f"  🏆 Current leader: {result.winner.title}")
        print(f"{'='*65}\n")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _row_to_proposal(self, r: sqlite3.Row) -> Proposal:
        return Proposal(
            proposal_id=r["proposal_id"],
            session_id=r["session_id"],
            author_id=r["author_id"],
            author_name=r["author_name"],
            title=r["title"],
            description=r["description"],
            experiment=json.loads(r["experiment"] or "{}"),
            status=ProposalStatus(r["status"]),
            created_at=r["created_at"],
            score_target=r["score_target"],
            metadata=json.loads(r["metadata"] or "{}"),
        )

    def _attach_vote_tallies(
        self, proposals: List[Proposal], session_id: str
    ) -> List[Proposal]:
        """Joins vote tallies onto proposals."""
        conn = self._conn()
        rows = conn.execute("""
            SELECT proposal_id, choice, SUM(weight) as total_weight
            FROM roundtable_votes
            WHERE session_id=?
            GROUP BY proposal_id, choice
        """, (session_id,)).fetchall()
        conn.close()
        tally_map: Dict[str, Dict[str, float]] = {}
        for r in rows:
            pid = r["proposal_id"]
            if pid not in tally_map:
                tally_map[pid] = {"YES": 0.0, "NO": 0.0, "ABSTAIN": 0.0}
            tally_map[pid][r["choice"]] = r["total_weight"]
        for p in proposals:
            t = tally_map.get(p.proposal_id, {})
            p.yes_weight     = t.get("YES", 0.0)
            p.no_weight      = t.get("NO", 0.0)
            p.abstain_weight = t.get("ABSTAIN", 0.0)
        return proposals
