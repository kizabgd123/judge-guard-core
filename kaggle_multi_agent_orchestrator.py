#!/usr/bin/env python3
"""
kaggle_multi_agent_orchestrator.py
==================================
Command-line orchestrator for Kaggle Multi-Agent Collaboration.
Implements the multi-agent system described by Kaggle #1 competitor Chris Deot:
- Agent Forum: Multi-agent discussion board
- Agent Mailbox: Direct agent-to-agent messaging with payloads and priorities
- Agent Hierarchy: Manager-Employee task delegation tree
- Round-Table: Consensus-driven experiment selection with weighted voting

Authority: MASTER_ORCHESTRATION.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.multi_agent import (
    AgentBase,
    AgentRole,
    AgentForum,
    AgentMailbox,
    MessagePriority,
    AgentHierarchy,
    TaskStatus,
    RoundTable,
    VoteChoice,
    ProposalStatus,
    KaggleManager,
    KaggleResearcher,
    KaggleEngineer,
    KaggleValidator,
    KaggleReviewer,
    KaggleObserver,
    SessionHandoffManager,
    AgentDialogueEngine,
)


# ---------------------------------------------------------------------------
# Default Team Instantiation
# ---------------------------------------------------------------------------

def get_default_team():
    manager = KaggleManager("manager_chris", "Manager Chris")
    researcher = KaggleResearcher("researcher_fable", "Researcher Fable")
    engineer = KaggleEngineer("engineer_opus", "Engineer Opus")
    validator = KaggleValidator("validator_guard", "Validator Guard")
    reviewer = KaggleReviewer("reviewer_codex", "Reviewer Codex")
    observer = KaggleObserver("observer_pi", "Observer Pi")
    return {
        "manager": manager,
        "researcher": researcher,
        "engineer": engineer,
        "validator": validator,
        "reviewer": reviewer,
        "observer": observer,
    }


def find_agent(agent_id: str) -> AgentBase:
    team = get_default_team()
    for a in team.values():
        if a.agent_id == agent_id:
            return a
    # Fallback generic agent
    return AgentBase(agent_id, agent_id, AgentRole.OBSERVER)


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

def handle_demo(args):
    """Executes a full multi-agent collaborative cycle inspired by Chris Deot's post."""
    print("\n" + "=" * 70)
    print("🚀 LAUNCHING KAGGLE MULTI-AGENT COLLABORATION DEMO")
    print("   Architecture: Chris Deot Multi-Agent Grandmaster Workflow")
    print("   Components: Forum, Mailbox, Hierarchy, Round-Table")
    print("=" * 70)

    team = get_default_team()
    manager = team["manager"]
    researcher = team["researcher"]
    engineer = team["engineer"]
    validator = team["validator"]
    reviewer = team["reviewer"]
    observer = team["observer"]

    competition = "name_that_llm"
    forum = AgentForum(forum_name=competition)
    mailbox = AgentMailbox()
    hierarchy = AgentHierarchy(team_name=competition)
    roundtable = RoundTable(competition=competition)

    # 1. Setup Hierarchy
    print("\n[STEP 1] Setting up Manager-Employee Hierarchy...")
    hierarchy.register_employee(manager, researcher)
    hierarchy.register_employee(manager, engineer)
    hierarchy.register_employee(manager, validator)
    hierarchy.register_employee(manager, reviewer)
    print("  ✓ Manager Chris registered 4 direct reports: Fable, Opus, Guard, Codex.")

    # 2. Forum: Manager creates discussion thread
    print("\n[STEP 2] Forum Discussion: Manager initiates research thread...")
    thread_id = forum.create_thread(
        agent=manager,
        title="Strategy Session: SOTA Breakthrough beyond 0.604",
        tags=["sota", "lora", "invariants"],
        pinned=True
    )
    print(f"  ✓ Thread created: {thread_id} — 'Strategy Session: SOTA Breakthrough beyond 0.604'")

    # 3. Forum: Agents discuss ideas
    print("\n[STEP 3] Multi-agent Forum discussion (Chris Deot observation: agents chatting)...")
    post1 = forum.post(
        agent=researcher,
        thread_id=thread_id,
        body="Chris mentioned we need to inspect the curly quote invariant. Across 1,049 Claude and GLM rows, curly quotes appear 0 times!"
    )
    print(f"  💬 [Researcher Fable]: {post1}")

    post2 = forum.reply(
        agent=reviewer,
        thread_id=thread_id,
        parent_post_id=post1,
        body="I verified the data. Also, Hungarian bipartite matching resolves 100% of prompt model collisions. Do you think Chris will like an ensemble of both?"
    )
    print(f"  💬 [Reviewer Codex]: {post2}")

    forum.react(agent=manager, post_id=post1, emoji="🔥")
    forum.react(agent=engineer, post_id=post2, emoji="👍")
    print("  ✓ Reactions posted: Manager reacted 🔥, Engineer reacted 👍")

    # 4. Round-Table Session & Proposals
    print("\n[STEP 4] Round-Table: Convening agents for next experiment selection...")
    session_id = roundtable.create_session(
        creator=manager,
        topic="Select Architecture for Submission 16 (Target 0.612+)"
    )
    print(f"  ✓ Round-Table Session: {session_id}")

    prop1 = roundtable.propose(
        agent=researcher,
        session_id=session_id,
        title="Proposition A: Extended Typographical Invariants + Multi-Cluster Hungarian",
        description="Zero out Claude/GLM on curly quotes, enforce 1-to-1 prompt Hungarian matching on cluster sizes 9-18.",
        experiment={"method": "invariants_hungarian", "target_score": 0.612},
        score_target=0.612
    )
    print(f"  💡 Proposal 1 submitted by Researcher Fable: {prop1}")

    prop2 = roundtable.propose(
        agent=engineer,
        session_id=session_id,
        title="Proposition B: Dual-Trunk 14B LoRA + WPCA Gaussian Shared-Prompt Heads",
        description="Train dual-trunk backbones with 4-Gaussian stack and spaced em-dash filter.",
        experiment={"method": "dual_lora_wpca", "target_score": 0.608},
        score_target=0.608
    )
    print(f"  💡 Proposal 2 submitted by Engineer Opus: {prop2}")

    # 5. Round-Table Voting (Manager vote counts double)
    print("\n[STEP 5] Voting Phase: Agents submit weighted votes...")
    roundtable.vote(manager, session_id, prop1, VoteChoice.YES, rationale="Decisive statistical invariant with zero risk.")
    roundtable.vote(researcher, session_id, prop1, VoteChoice.YES, rationale="Backed by 1,049 row empirical validation.")
    roundtable.vote(reviewer, session_id, prop1, VoteChoice.YES, rationale="Eliminates cross-family drift.")
    roundtable.vote(engineer, session_id, prop2, VoteChoice.YES, rationale="Strongest raw deep learning representations.")
    roundtable.vote(validator, session_id, prop1, VoteChoice.YES, rationale="Provably zero-leakage transformation.")

    voting_result = roundtable.close_and_tally(manager, session_id)
    print(f"\n{voting_result}")

    # 6. Hierarchy Task Delegation
    print("\n[STEP 6] Hierarchy: Manager delegates winning experiment to Engineer...")
    task_id = hierarchy.assign_task(
        issuer=manager,
        to_agent=engineer,
        title="Implement & Build Kernel Sub-16",
        description=f"Implement winning proposal {voting_result.winner.title} targeting score {voting_result.winner.score_target}",
        priority=1,
        metadata={"proposal_id": voting_result.winner.proposal_id, "score_target": voting_result.winner.score_target}
    )
    print(f"  ✓ Task Assigned: {task_id} -> Engineer Opus")

    hierarchy.accept_task(engineer, task_id)
    hierarchy.start_task(engineer, task_id)
    print(f"  🤝 Engineer Opus accepted and started task {task_id}.")

    # Simulate execution and completion
    build_payload = {
        "kernel_slug": "ntl-sota-0612-apex-invariants-hungarian",
        "status": "BUILD_SUCCESS",
        "cv_score": 0.6124,
        "files_generated": ["kernel_sub16_sota_0612_apex_invariants_hungarian/notebook.ipynb"]
    }
    hierarchy.complete_task(engineer, task_id, result=build_payload, notes="Kernel built and validated.")
    print(f"  ✅ Engineer Opus completed task {task_id}.")

    # 7. Mailbox: Direct agent-to-agent communication
    print("\n[STEP 7] Mailbox: Engineer reports to Manager with payload via direct message...")
    msg_id = mailbox.send(
        sender=engineer,
        to_agent_id=manager.agent_id,
        to_agent_name=manager.name,
        subject="Kernel Sub-16 Build Complete (CV: 0.6124)",
        body="Manager Chris, the winning round-table kernel has been built and verified. Ready for Kaggle submission.",
        payload=build_payload,
        priority=MessagePriority.HIGH,
        cc=[validator.agent_id, reviewer.agent_id]
    )
    print(f"  📬 Message Sent: {msg_id} -> Manager Chris (CC: Validator Guard, Reviewer Codex)")

    # 8. Validator: Audits and posts to forum
    print("\n[STEP 8] Validator: Audit and validation check...")
    val_res = {
        "path": "kernel_sub16/submission.parquet",
        "valid": True,
        "actual_rows": 1500,
        "errors": []
    }
    v_post = validator.post_audit_report(forum, thread_id, val_res)
    print(f"  🛡️ Validator Guard posted audit report to forum: {v_post}")

    # 9. Observer: Polls leaderboard and logs telemetry
    print("\n[STEP 9] Observer: Logging leaderboard & telemetry status...")
    lb_data = {
        "competition": "name_that_llm",
        "polled_at": datetime.now(timezone.utc).isoformat(),
        "entries": [
            {"teamName": "Chris Deotte", "score": "0.604", "is_user": False},
            {"teamName": "kiza123123", "score": "0.612", "is_user": True},
            {"teamName": "SOTA Ensemble", "score": "0.598", "is_user": False},
        ]
    }
    obs_post = observer.post_leaderboard_update(forum, thread_id, lb_data)
    print(f"  📊 Observer Pi posted leaderboard standing to forum: {obs_post}")

    print("\n" + "=" * 70)
    print("✅ MULTI-AGENT COLLABORATION DEMO COMPLETED SUCCESSFULLY!")
    print("   All records persisted in SQLite research.db.")
    print("=" * 70 + "\n")


def handle_forum_list(args):
    forum = AgentForum(args.forum)
    threads = forum.list_threads()
    print(f"\n📋 Threads in forum '{args.forum}' ({len(threads)} total):")
    for t in threads:
        pin = "📌 " if t.pinned else "   "
        print(f"{pin}[{t.thread_id}] {t.title} (by {t.author_name}, {t.post_count} posts)")


def handle_forum_read(args):
    forum = AgentForum(args.forum)
    forum.print_thread(args.thread_id)


def handle_mailbox_inbox(args):
    agent = find_agent(args.agent_id)
    mailbox = AgentMailbox()
    mailbox.print_inbox(agent, unread_only=args.unread)


def handle_hierarchy_report(args):
    manager = find_agent(args.manager_id)
    hierarchy = AgentHierarchy(args.team)
    hierarchy.print_report(manager)


def handle_roundtable_view(args):
    roundtable = RoundTable(args.competition)
    roundtable.print_session(args.session_id)


def handle_handoff_write(args):
    agent = find_agent(args.author)
    manager = SessionHandoffManager(args.comp)
    rec = manager.record_discovery(
        agent=agent,
        session_id=f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        headline=args.headline,
        what_worked=args.worked,
        what_failed=args.failed,
        recommendations=args.recommend,
        metric_delta=args.metric_delta,
        invariants=args.invariants.split(",") if args.invariants else [],
        artifacts=args.artifacts.split(",") if args.artifacts else []
    )
    print(f"\n✅ Discovery file successfully created: {rec.discovery_id}")
    print(f"   Headline: {rec.headline}")
    print(f"   Delta: {rec.metric_delta:+.4f}")
    print(f"   Saved to exports/discoveries/\n")


def handle_handoff_read(args):
    team = get_default_team()
    manager = SessionHandoffManager(args.comp)
    briefing = manager.build_cumulative_briefing(team["manager"], limit=args.limit)
    print(f"\n{briefing}\n")


def handle_debate(args):
    print("\n" + "=" * 70)
    print(f"🗣️ LAUNCHING AUTONOMOUS AGENT DEBATE (Topic: {args.topic})")
    print(f"   User Reference: {args.user} | Rounds: {args.rounds}")
    print("=" * 70)
    team = get_default_team()
    forum = AgentForum(args.comp)

    # Create debate thread
    thread_id = forum.create_thread(
        agent=team["manager"],
        title=f"Debate: {args.topic}",
        tags=["debate", "strategy", "alignment"]
    )
    print(f"✓ Debate Thread Created: {thread_id}")

    from src.multi_agent.llm_dialogue import AgentDialogueEngine
    dialogue = AgentDialogueEngine(user_name=args.user)

    debate_agents = [team["manager"], team["researcher"], team["engineer"], team["validator"], team["reviewer"]]
    post_ids = dialogue.run_autonomous_debate(
        forum=forum,
        thread_id=thread_id,
        agents=debate_agents,
        rounds=args.rounds,
        topic_directive=f"Debate the following question thoroughly: '{args.topic}'. Formulate consensus for {args.user}."
    )
    print(f"✓ Generated {len(post_ids)} authentic in-character forum contributions.")
    forum.print_thread(thread_id)


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Kaggle Multi-Agent Collaboration Framework (Chris Deot Architecture)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # demo
    demo_p = subparsers.add_parser("demo", help="Run full multi-agent collaborative cycle demo")

    # debate
    deb_p = subparsers.add_parser("debate", help="Run autonomous live LLM agent debate on forum")
    deb_p.add_argument("--topic", default="Should we commit our single GPU submission slot to Hungarian Bipartite Matching vs Stylometric Ensembling?", help="Debate topic")
    deb_p.add_argument("--rounds", type=int, default=1, help="Number of debate rounds")
    deb_p.add_argument("--user", default="Chris", help="User name referenced in agent dialogue")
    deb_p.add_argument("--comp", default="name_that_llm", help="Competition name")

    # handoff
    hand_p = subparsers.add_parser("handoff", help="Session handoff & discovery file commands")
    hand_sub = hand_p.add_subparsers(dest="hand_cmd")

    h_write = hand_sub.add_parser("write", help="Write a discovery file after a session")
    h_write.add_argument("--author", default="researcher_fable", help="Author agent ID")
    h_write.add_argument("--headline", required=True, help="Discovery headline")
    h_write.add_argument("--worked", required=True, help="What worked")
    h_write.add_argument("--failed", required=True, help="What failed")
    h_write.add_argument("--recommend", required=True, help="Recommendations for next agent")
    h_write.add_argument("--metric-delta", type=float, default=0.0, help="Metric delta")
    h_write.add_argument("--invariants", default="", help="Comma-separated invariants")
    h_write.add_argument("--artifacts", default="", help="Comma-separated artifact paths")
    h_write.add_argument("--comp", default="name_that_llm", help="Competition name")

    h_read = hand_sub.add_parser("read", help="Read past cumulative discoveries")
    h_read.add_argument("--comp", default="name_that_llm", help="Competition name")
    h_read.add_argument("--limit", type=int, default=5, help="Number of past sessions to ingest")

    # forum
    forum_p = subparsers.add_parser("forum", help="Forum commands")
    forum_sub = forum_p.add_subparsers(dest="forum_cmd")

    f_list = forum_sub.add_parser("list", help="List forum threads")
    f_list.add_argument("--forum", default="name_that_llm", help="Forum name")

    f_read = forum_sub.add_parser("read", help="Read a thread")
    f_read.add_argument("thread_id", help="Thread ID")
    f_read.add_argument("--forum", default="name_that_llm", help="Forum name")

    # mailbox
    mail_p = subparsers.add_parser("mailbox", help="Mailbox commands")
    mail_sub = mail_p.add_subparsers(dest="mail_cmd")

    m_inbox = mail_sub.add_parser("inbox", help="Check agent inbox")
    m_inbox.add_argument("agent_id", help="Agent ID")
    m_inbox.add_argument("--unread", action="store_true", help="Unread only")

    # hierarchy
    hier_p = subparsers.add_parser("hierarchy", help="Hierarchy commands")
    hier_sub = hier_p.add_subparsers(dest="hier_cmd")

    h_rep = hier_sub.add_parser("report", help="Print team status report")
    h_rep.add_argument("--manager-id", default="manager_chris", help="Manager ID")
    h_rep.add_argument("--team", default="name_that_llm", help="Team name")

    # roundtable
    rt_p = subparsers.add_parser("roundtable", help="Round-Table commands")
    rt_sub = rt_p.add_subparsers(dest="rt_cmd")

    rt_view = rt_sub.add_parser("view", help="View round-table session")
    rt_view.add_argument("session_id", help="Session ID")
    rt_view.add_argument("--competition", default="name_that_llm", help="Competition name")

    args = parser.parse_args()

    if args.command == "demo":
        handle_demo(args)
    elif args.command == "debate":
        handle_debate(args)
    elif args.command == "handoff":
        if args.hand_cmd == "write":
            handle_handoff_write(args)
        elif args.hand_cmd == "read":
            handle_handoff_read(args)
        else:
            hand_p.print_help()
    elif args.command == "forum":
        if args.forum_cmd == "list":
            handle_forum_list(args)
        elif args.forum_cmd == "read":
            handle_forum_read(args)
        else:
            forum_p.print_help()
    elif args.command == "mailbox":
        if args.mail_cmd == "inbox":
            handle_mailbox_inbox(args)
        else:
            mail_p.print_help()
    elif args.command == "hierarchy":
        if args.hier_cmd == "report":
            handle_hierarchy_report(args)
        else:
            hier_p.print_help()
    elif args.command == "roundtable":
        if args.rt_cmd == "view":
            handle_roundtable_view(args)
        else:
            rt_p.print_help()
    else:
        # Default to running the demo if no args provided
        handle_demo(args)


if __name__ == "__main__":
    main()
