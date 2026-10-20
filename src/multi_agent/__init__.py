"""
Kaggle Multi-Agent Collaboration Framework
==========================================
Inspired by Chris Deot (#1 Name That LLM) multi-agent architecture:
- Agent Forum   — multi-agent SQLite-backed chat/discussion
- Mailbox       — direct agent-to-agent message passing
- Hierarchy     — manager-employee task delegation tree
- Round-Table   — voting-based consensus for experiment selection

All state is persisted in research.db (existing SQLite).
Authority: MASTER_ORCHESTRATION.md
"""

from .agent_base import AgentBase, AgentRole
from .forum import AgentForum
from .mailbox import AgentMailbox, MessagePriority
from .hierarchy import AgentHierarchy, TaskStatus
from .roundtable import RoundTable, VoteChoice, ProposalStatus
from .kaggle_agents import (
    KaggleManager,
    KaggleResearcher,
    KaggleEngineer,
    KaggleValidator,
    KaggleReviewer,
    KaggleObserver,
)
from .session_handoff import SessionHandoffManager, DiscoveryRecord
from .llm_dialogue import AgentDialogueEngine

__all__ = [
    "AgentBase",
    "AgentRole",
    "AgentForum",
    "AgentMailbox",
    "MessagePriority",
    "AgentHierarchy",
    "TaskStatus",
    "RoundTable",
    "VoteChoice",
    "ProposalStatus",
    "KaggleManager",
    "KaggleResearcher",
    "KaggleEngineer",
    "KaggleValidator",
    "KaggleReviewer",
    "KaggleObserver",
    "SessionHandoffManager",
    "DiscoveryRecord",
    "AgentDialogueEngine",
]
