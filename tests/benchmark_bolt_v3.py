import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies to avoid actual LLM calls
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

# Create a temporary WORK_LOG.md for testing
WORK_LOG_PATH = "TEST_WORK_LOG.md"

def setup_test_env():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Benchmark Action\n")

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)

def run_benchmark():
    # We want to measure the overhead of push_verdict and initialization
    # Mock evaluate to be fast
    with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True), \
         patch('src.antigravity_core.gemini_client.GeminiClient.judge_content', return_value=True):

        from judge_guard import JudgeGuard
        import judge_guard
        judge_guard.JUDGE_AVAILABLE = True

        # Measure initialization
        start_init = time.time()
        guard = JudgeGuard(work_log_path=WORK_LOG_PATH)
        end_init = time.time()
        print(f"JudgeGuard Initialization: {end_init - start_init:.4f}s")

        action = "Benchmarked Action"

        # Measure verify_action (focusing on non-LLM overhead)
        # We call it multiple times to average
        iterations = 5
        total_time = 0
        for i in range(iterations):
            # Reset work log timestamp to stay fresh
            os.utime(WORK_LOG_PATH, None)

            start = time.time()
            guard.verify_action(action)
            end = time.time()
            total_time += (end - start)
            print(f"Iteration {i+1} duration: {end - start:.4f}s")

        print(f"Average verify_action duration: {total_time / iterations:.4f}s")

if __name__ == "__main__":
    setup_test_env()
    try:
        run_benchmark()
    finally:
        cleanup_test_env()
