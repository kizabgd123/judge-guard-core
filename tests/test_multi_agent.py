"""
tests/test_multi_agent.py
=========================
Comprehensive unit and integration test suite for the Kaggle Multi-Agent
Collaboration Framework (Chris Deot architecture).

Uses standard unittest.TestCase for zero-dependency execution.

Covers:
- AgentBase registry, roles, heartbeats
- AgentForum threads, posts, replies, reactions
- AgentMailbox message passing, priorities, payloads, CC, read status
- AgentHierarchy task assignment, lifecycle transitions, team reports
- RoundTable proposals, weighted voting (2x manager weight), tally, winner declaration
- Specialized Kaggle agents (Manager, Researcher, Engineer, Validator, Reviewer, Observer)

Authority: MASTER_ORCHESTRATION.md
"""

import json
import sqlite3
import unittest
from pathlib import Path

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
)


class TestAgentBaseAndRegistry(unittest.TestCase):
    def test_agent_base_registration(self):
        agent = AgentBase("test_agent_01", "Agent Alpha", AgentRole.RESEARCHER)
        self.assertEqual(agent.agent_id, "test_agent_01")
        self.assertEqual(agent.role, AgentRole.RESEARCHER)

        agent.heartbeat()
        agents = AgentBase.list_agents(role=AgentRole.RESEARCHER)
        agent_ids = [a["agent_id"] for a in agents]
        self.assertIn("test_agent_01", agent_ids)
        agent.close()

    def test_specialized_agents_roles_and_caps(self):
        manager = KaggleManager("mgr_test", "Test Manager")
        researcher = KaggleResearcher("res_test", "Test Researcher")
        engineer = KaggleEngineer("eng_test", "Test Engineer")
        validator = KaggleValidator("val_test", "Test Validator")
        reviewer = KaggleReviewer("rev_test", "Test Reviewer")
        observer = KaggleObserver("obs_test", "Test Observer")

        self.assertEqual(manager.role, AgentRole.MANAGER)
        self.assertEqual(researcher.role, AgentRole.RESEARCHER)
        self.assertEqual(engineer.role, AgentRole.ENGINEER)
        self.assertEqual(validator.role, AgentRole.VALIDATOR)
        self.assertEqual(reviewer.role, AgentRole.REVIEWER)
        self.assertEqual(observer.role, AgentRole.OBSERVER)

        self.assertTrue(any(c.name == "task_issuance" for c in manager.capabilities))
        self.assertTrue(any(c.name == "kernel_analysis" for c in researcher.capabilities))
        self.assertTrue(any(c.name == "kernel_push" for c in engineer.capabilities))
        self.assertTrue(any(c.name == "invariant_audit" for c in validator.capabilities))
        self.assertTrue(any(c.name == "proposal_authoring" for c in reviewer.capabilities))
        self.assertTrue(any(c.name == "leaderboard_polling" for c in observer.capabilities))

        manager.close()
        researcher.close()
        engineer.close()
        validator.close()
        reviewer.close()
        observer.close()


class TestAgentForum(unittest.TestCase):
    def test_forum_threads_posts_reactions(self):
        forum = AgentForum("test_competition_forum")
        author1 = AgentBase("author_01", "Author 1", AgentRole.RESEARCHER)
        author2 = AgentBase("author_02", "Author 2", AgentRole.ENGINEER)

        # 1. Create thread
        thread_id = forum.create_thread(
            author1, "Exploring Invariant Filters", tags=["stylometry", "sota"], pinned=True
        )
        self.assertTrue(thread_id.startswith("thread_"))

        threads = forum.list_threads()
        self.assertTrue(any(t.thread_id == thread_id for t in threads))

        # 2. Post top-level message
        post_id = forum.post(author1, thread_id, "Curly quotes never appear in Claude or GLM rows.")
        self.assertTrue(post_id.startswith("post_"))

        # 3. Reply to post
        reply_id = forum.reply(author2, thread_id, post_id, "Confirmed! Let's test Hungarian matching too.")
        self.assertTrue(reply_id.startswith("post_"))

        # 4. Reactions
        forum.react(author1, post_id, "🔥")
        posts = forum.read_thread(thread_id)
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0].post_id, post_id)
        self.assertIn("author_01", posts[0].reactions.get("🔥", []))

        # Toggle reaction off
        forum.react(author1, post_id, "🔥")
        posts_after = forum.read_thread(thread_id)
        self.assertNotIn("author_01", posts_after[0].reactions.get("🔥", []))

        author1.close()
        author2.close()

    def test_forum_list_threads_tag_filtering(self):
        forum = AgentForum("test_tag_filtering_forum")
        author = AgentBase("author_tag", "Tag Author", AgentRole.RESEARCHER)

        # Create 30 threads: first 10 have "rare_tag", rest 20 have "common_tag"
        for i in range(30):
            tags = ["rare_tag"] if i < 10 else ["common_tag"]
            forum.create_thread(author, f"Thread {i}", tags=tags)

        # Tag filtering pushed into SQLite should return up to limit (10) rare_tag threads
        rare_threads = forum.list_threads(limit=10, tags=["rare_tag"])
        self.assertEqual(len(rare_threads), 10)
        self.assertTrue(all("rare_tag" in t.tags for t in rare_threads))

        author.close()


class TestAgentMailbox(unittest.TestCase):
    def test_mailbox_message_passing(self):
        mailbox = AgentMailbox()
        sender = AgentBase("sender_01", "Sender", AgentRole.MANAGER)
        receiver = AgentBase("receiver_01", "Receiver", AgentRole.ENGINEER)
        cc_agent = AgentBase("cc_01", "Auditor", AgentRole.VALIDATOR)

        payload = {"kernel": "sub16", "cv": 0.6124}
        msg_id = mailbox.send(
            sender=sender,
            to_agent_id=receiver.agent_id,
            to_agent_name=receiver.name,
            subject="Action Required: Sub-16 Review",
            body="Please review Hungarian matching convergence.",
            payload=payload,
            priority=MessagePriority.HIGH,
            cc=[cc_agent.agent_id],
        )
        self.assertTrue(msg_id.startswith("msg_"))

        # Receiver inbox check
        inbox = mailbox.inbox(receiver, unread_only=True)
        self.assertTrue(any(m.message_id == msg_id for m in inbox))
        target_msg = next(m for m in inbox if m.message_id == msg_id)
        self.assertEqual(target_msg.payload, payload)
        self.assertEqual(target_msg.priority, MessagePriority.HIGH)

        # Mark read
        mailbox.mark_read(msg_id)
        self.assertEqual(mailbox.unread_count(receiver), 0)

        # CC agent received message
        cc_inbox = mailbox.inbox(cc_agent, unread_only=False)
        self.assertTrue(any("[CC]" in m.subject for m in cc_inbox))

        sender.close()
        receiver.close()
        cc_agent.close()


class TestAgentHierarchy(unittest.TestCase):
    def test_hierarchy_lifecycle(self):
        hierarchy = AgentHierarchy("test_team")
        manager = KaggleManager("mgr_h", "Manager H")
        engineer = KaggleEngineer("eng_h", "Engineer H")

        # Register relationship
        hierarchy.register_employee(manager, engineer)
        employees = hierarchy.get_employees(manager)
        self.assertTrue(any(e["agent_id"] == "eng_h" for e in employees))

        # Assign task
        task_id = hierarchy.assign_task(
            issuer=manager,
            to_agent=engineer,
            title="Build Sub-17",
            description="Dual LoRA + Hungarian",
            priority=1,
        )
        self.assertTrue(task_id.startswith("task_"))

        # Lifecycle transitions
        my_tasks = hierarchy.my_tasks(engineer, status=TaskStatus.PENDING)
        self.assertTrue(any(t.task_id == task_id for t in my_tasks))

        hierarchy.accept_task(engineer, task_id)
        self.assertTrue(any(t.task_id == task_id for t in hierarchy.my_tasks(engineer, status=TaskStatus.ACCEPTED)))

        hierarchy.start_task(engineer, task_id)
        self.assertTrue(any(t.task_id == task_id for t in hierarchy.my_tasks(engineer, status=TaskStatus.IN_PROGRESS)))

        hierarchy.complete_task(engineer, task_id, result={"status": "OK", "score": 0.615})
        done_tasks = hierarchy.my_tasks(engineer, status=TaskStatus.DONE)
        done_task = next(t for t in done_tasks if t.task_id == task_id)
        self.assertEqual(done_task.result, {"status": "OK", "score": 0.615})

        report = hierarchy.team_status_report(manager)
        self.assertGreaterEqual(report["total_tasks"], 1)
        self.assertIn("DONE", report["by_status"])

        manager.close()
        engineer.close()


class TestRoundTableVoting(unittest.TestCase):
    def test_roundtable_voting_weighted_winner(self):
        roundtable = RoundTable("test_comp")
        manager = KaggleManager("mgr_rt", "Manager RT")
        res1 = KaggleResearcher("res_rt1", "Researcher 1")
        res2 = KaggleResearcher("res_rt2", "Researcher 2")

        session_id = roundtable.create_session(manager, "Round 16 Architectural Consensus")
        self.assertTrue(session_id.startswith("rt_"))

        # Proposals
        prop_a = roundtable.propose(
            res1, session_id,
            title="Proposition A: Curly-Quote Invariants",
            description="Zero out Claude/GLM on curly quotes",
            score_target=0.612,
        )
        prop_b = roundtable.propose(
            res2, session_id,
            title="Proposition B: Baseline GBDT",
            description="Simple LightGBM baseline",
            score_target=0.559,
        )

        # Voting:
        # Manager votes for prop_a (Manager weight = 2.0)
        roundtable.vote(manager, session_id, prop_a, VoteChoice.YES, rationale="High signal")
        # Res1 votes for prop_a (weight = 1.0)
        roundtable.vote(res1, session_id, prop_a, VoteChoice.YES, rationale="Empirical evidence")
        # Res2 votes for prop_b (weight = 1.0)
        roundtable.vote(res2, session_id, prop_b, VoteChoice.YES, rationale="Simple")

        result = roundtable.close_and_tally(manager, session_id)
        self.assertIsNotNone(result.winner)
        self.assertEqual(result.winner.proposal_id, prop_a)
        # prop_a: 2.0 (mgr) + 1.0 (res1) = 3.0 weight
        self.assertEqual(result.winner.yes_weight, 3.0)
        self.assertEqual(result.winner.status, ProposalStatus.WINNER)

        # Verify prop_b marked as rejected
        proposals = roundtable.list_proposals(session_id)
        pb = next(p for p in proposals if p.proposal_id == prop_b)
        self.assertEqual(pb.status, ProposalStatus.REJECTED)

        manager.close()
        res1.close()
        res2.close()


class TestSessionHandoff(unittest.TestCase):
    def test_record_discovery_and_cumulative_briefing(self):
        from src.multi_agent.session_handoff import SessionHandoffManager
        manager_agent = KaggleManager("mgr_handoff", "Manager Handoff")
        engineer_agent = KaggleEngineer("eng_handoff", "Engineer Handoff")
        handoff = SessionHandoffManager(competition="test_comp_handoff")

        rec = handoff.record_discovery(
            agent=engineer_agent,
            session_id="session_test_01",
            headline="Discovered Spaced Em-Dash Invariant in Claude Opus",
            what_worked="Spaced em-dash guard achieves 100% precision on Opus and GLM.",
            what_failed="Linear blending without Sinkhorn balancing causes probability skew.",
            recommendations="Enforce bipartite Hungarian matching on top of em-dash filtering.",
            invariants=["spaced_em_dash", "curly_quote_zero"],
            artifacts=["kernel_sub16.py"],
            metric_delta=+0.053,
        )

        self.assertTrue(rec.discovery_id.startswith("disc_"))
        self.assertEqual(rec.metric_delta, +0.053)

        past = handoff.read_past_discoveries()
        self.assertTrue(any(d.discovery_id == rec.discovery_id for d in past))

        briefing = handoff.build_cumulative_briefing(manager_agent)
        self.assertIn("Spaced Em-Dash", briefing)
        self.assertIn("Manager Handoff", briefing)

        manager_agent.close()
        engineer_agent.close()


class TestLLMDialogue(unittest.TestCase):
    def test_agent_dialogue_generation(self):
        import os
        from src.multi_agent.llm_dialogue import AgentDialogueEngine
        dialogue = AgentDialogueEngine(user_name="Chris")
        researcher = KaggleResearcher("res_dialogue", "Researcher Fable")
        forum = AgentForum("test_dialogue_forum")

        thread_id = forum.create_thread(
            researcher, "Hypothesis on Hungarian Matching", tags=["discussion"]
        )

        thought = dialogue.generate_agent_thought(
            agent=researcher,
            thread_title="Hypothesis on Hungarian Matching",
            recent_posts=[{"author_name": "Manager Chris", "role": "manager", "body": "What does Chris want us to test?"}],
            prompt_directive="Express your perspective on Hungarian matching.",
            allow_fallback=True
        )

        self.assertIsInstance(thought, str)
        self.assertGreater(len(thought), 15)

        # Verify strict mode: when allow_fallback=False and no API key is configured,
        # it must raise RuntimeError rather than silently faking success
        if not os.getenv("GEMINI_API_KEY") and not os.getenv("GEMINI_API_KEYS"):
            with self.assertRaises(RuntimeError):
                dialogue.generate_agent_thought(
                    agent=researcher,
                    thread_title="Hypothesis on Hungarian Matching",
                    recent_posts=[],
                    allow_fallback=False
                )

        post_id = forum.post(researcher, thread_id, thought)
        posts = forum.read_thread(thread_id)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].post_id, post_id)

        researcher.close()


if __name__ == "__main__":
    unittest.main()
