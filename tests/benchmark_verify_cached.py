import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Mock ResearchPipeline to avoid real DB hits for now, or use a temp one
# Actually, let's mock it to see the overhead of JudgeGuard itself.

from judge_guard import JudgeGuard

WORK_LOG_PATH = "TEST_WORK_LOG.md"

def setup_test_env():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Benchmark Action\n")

    # MASTER_ORCHESTRATION.md
    rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    with open(rules_path, "w") as f:
        f.write("# Master Rules\n")

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)

def run_benchmark():
    guard = JudgeGuard(work_log_path=WORK_LOG_PATH)

    # Mock pipeline for cache hit
    mock_pipeline = MagicMock()
    mock_pipeline.get_cached_verdict.return_value = "PASSED"
    guard._pipeline = mock_pipeline

    # Mock bridge
    with patch('src.antigravity_core.mobile_bridge.bridge') as mock_bridge:
        action = "Test cached action"

        # Warm up
        guard.verify_action(action)

        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            guard.verify_action(action)
        end = time.time()

        avg_time = (end - start) / iterations
        print(f"Average verify_action (cached hit) time: {avg_time*1000:.4f}ms")

if __name__ == "__main__":
    setup_test_env()
    try:
        run_benchmark()
    finally:
        cleanup_test_env()
