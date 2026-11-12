import time
import os
import sys
import unittest

# Ensure src is in path
sys.path.append(os.getcwd())

from src.multi_agent.roundtable import RoundTable, VoteChoice
from src.multi_agent.agent_base import AgentBase, AgentRole


class BenchmarkRoundTable(unittest.TestCase):
    def test_list_proposals_performance(self):
        class DummyAgent(AgentBase):
            def run_cycle(self):
                pass

        manager = DummyAgent("m_bench", "Manager", AgentRole.MANAGER)
        engineer = DummyAgent("e_bench", "Engineer", AgentRole.ENGINEER)

        rt = RoundTable(competition="benchmark_comp")
        session_id = rt.create_session(manager, "Benchmark Session Topic")

        # Propose 20 ideas and cast votes
        p_ids = [
            rt.propose(engineer, session_id, f"Proposal {i}", f"Description {i}", score_target=0.6 + i * 0.001)
            for i in range(20)
        ]
        for p in p_ids:
            rt.vote(manager, session_id, p, VoteChoice.YES, rationale="Manager approval")
            rt.vote(engineer, session_id, p, VoteChoice.NO, rationale="Engineer hesitation")

        # Baseline: simulate separate queries like the unoptimized implementation
        def list_proposals_unoptimized(sid):
            conn = rt._conn()
            rows = conn.execute(
                "SELECT * FROM roundtable_proposals WHERE session_id=? ORDER BY created_at ASC",
                (sid,)
            ).fetchall()
            conn.close()
            props = [rt._row_to_proposal(r) for r in rows]
            return rt._attach_vote_tallies(props, sid)

        # Functional equivalence test
        unopt_results = list_proposals_unoptimized(session_id)
        opt_results = rt.list_proposals(session_id)
        self.assertEqual(len(unopt_results), len(opt_results))
        for u, o in zip(unopt_results, opt_results):
            self.assertEqual(u.proposal_id, o.proposal_id)
            self.assertEqual(u.title, o.title)
            self.assertEqual(u.yes_weight, o.yes_weight)
            self.assertEqual(u.no_weight, o.no_weight)
            self.assertEqual(u.abstain_weight, o.abstain_weight)

        # Benchmark unoptimized
        iterations = 200
        start = time.perf_counter()
        for _ in range(iterations):
            list_proposals_unoptimized(session_id)
        t_unopt = time.perf_counter() - start

        # Benchmark optimized
        start = time.perf_counter()
        for _ in range(iterations):
            rt.list_proposals(session_id)
        t_opt = time.perf_counter() - start

        pct_reduction = ((t_unopt - t_opt) / t_unopt) * 100.0
        speedup = t_unopt / t_opt

        print(f"\n--- RoundTable.list_proposals Benchmark ({iterations} iterations) ---")
        print(f"Unoptimized latency: {t_unopt * 1000:.2f} ms ({t_unopt / iterations * 1000:.3f} ms/call)")
        print(f"Optimized latency:   {t_opt * 1000:.2f} ms ({t_opt / iterations * 1000:.3f} ms/call)")
        print(f"Speedup:             {speedup:.2f}x ({pct_reduction:.1f}% latency reduction)")

        self.assertLess(t_opt, t_unopt)


if __name__ == "__main__":
    unittest.main()
