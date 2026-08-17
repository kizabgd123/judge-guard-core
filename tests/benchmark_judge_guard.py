import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies to avoid import errors
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Now we can import things
import src.antigravity_core.judge_flow
import src.antigravity_core.gemini_client
import src.antigravity_core.mobile_bridge

# Create a temporary WORK_LOG.md for testing
WORK_LOG_PATH = "TEST_WORK_LOG.md"

def setup_test_env():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Benchmark Action\n")

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)

def run_benchmark():
    # Mocking dependencies to simulate LLM latency
    with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate') as mock_eval, \
         patch('src.antigravity_core.gemini_client.GeminiClient.judge_content') as mock_judge, \
         patch('src.antigravity_core.mobile_bridge.bridge.push_verdict'):

        # Simulate 0.5s latency for LLM
        def slow_evaluate(*args, **kwargs):
            time.sleep(0.5)
            return True

        mock_eval.side_effect = slow_evaluate
        mock_judge.return_value = True

        from judge_guard import JudgeGuard
        # We need to force JUDGE_AVAILABLE to be true in the judge_guard module
        import judge_guard
        judge_guard.JUDGE_AVAILABLE = True

        guard = JudgeGuard(work_log_path=WORK_LOG_PATH)

        action = "Benchmarked Action"

        print(f"\n--- Benchmarking JudgeGuard.verify_action for: '{action}' ---")

        # First call (Cold)
        start = time.time()
        res1 = guard.verify_action(action)
        end = time.time()
        print(f"Cold Call duration: {end - start:.4f}s (Result: {res1})")

        # Second call (Warm - currently should still be slow)
        start = time.time()
        res2 = guard.verify_action(action)
        end = time.time()
        print(f"Warm Call duration: {end - start:.4f}s (Result: {res2})")

if __name__ == "__main__":
    setup_test_env()
    try:
        run_benchmark()
    finally:
        cleanup_test_env()
