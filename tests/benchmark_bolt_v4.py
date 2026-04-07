import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies to avoid import errors and network calls
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
# sys.modules['requests'] = MagicMock() # We want to see subprocess overhead, so don't mock requests globally yet
sys.modules['dotenv'] = MagicMock()

import judge_guard

# Create a temporary WORK_LOG.md for testing
WORK_LOG_PATH = "TEST_WORK_LOG_BOLT.md"

def setup_test_env():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Research Action\n")

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)
    if os.path.exists(".cache/notion_queue.json"):
        # Don't delete, might be important. But for test we might want to.
        pass

def run_benchmark():
    # Mocking dependencies to simulate LLM latency
    # We want to isolate the overhead of _sync_to_notion
    with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate') as mock_eval, \
         patch('src.antigravity_core.gemini_client.GeminiClient.judge_content') as mock_judge, \
         patch('src.antigravity_core.mobile_bridge.bridge.push_verdict'), \
         patch('src.antigravity_core.gemini_client.GeminiClient.generate_content') as mock_gen:

        mock_eval.return_value = True
        mock_judge.return_value = True
        mock_gen.return_value = "PASSED"

        # Force JUDGE_AVAILABLE
        judge_guard.JUDGE_AVAILABLE = True

        # We also need to mock ResearchPipeline.sync_to_notion to avoid real network calls
        # but we want to see the overhead of spawning the subprocess.
        # Actually, the subprocess call runs 'research_pipeline.py' which will try to sync.
        # If we don't have NOTION_TOKEN, it just writes to file. That's fine for measuring overhead.

        guard = judge_guard.JudgeGuard(work_log_path=WORK_LOG_PATH)

        # This action triggers _sync_to_notion
        action = "Research Phase 1: Discovery"

        print(f"\n--- Benchmarking JudgeGuard.verify_action (with subprocess sync) ---")

        iterations = 3
        durations = []
        for i in range(iterations):
            # Clear cache between runs if we want to measure sync every time
            if guard.pipeline:
                guard.pipeline.conn.execute("DELETE FROM verdicts")
                guard.pipeline.conn.commit()

            start = time.time()
            res = guard.verify_action(action)
            end = time.time()
            durations.append(end - start)
            print(f"Iteration {i+1}: {end - start:.4f}s")

        avg_duration = sum(durations) / len(durations)
        print(f"Average duration: {avg_duration:.4f}s")

if __name__ == "__main__":
    setup_test_env()
    try:
        run_benchmark()
    finally:
        cleanup_test_env()
