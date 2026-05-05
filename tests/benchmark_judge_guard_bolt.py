import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

from judge_guard import JudgeGuard

WORK_LOG_PATH = "WORK_LOG_BENCHMARK.md"

def setup():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Benchmark Action\n")
    # Touch it to make it fresh
    os.utime(WORK_LOG_PATH, None)

def cleanup():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)

def benchmark():
    setup()
    try:
        guard = JudgeGuard(work_log_path=WORK_LOG_PATH)

        # Mock pipeline to return a cached verdict
        mock_pipeline = MagicMock()
        mock_pipeline.get_cached_verdict.return_value = "PASSED"
        guard._pipeline = mock_pipeline

        action = "Cached Action"

        # Warm up
        guard.verify_action(action)

        start = time.perf_counter()
        iterations = 1000
        for _ in range(iterations):
            guard.verify_action(action)
        end = time.perf_counter()

        avg_time = (end - start) / iterations
        print(f"Average Cached Verification Latency: {avg_time*1000:.4f} ms")

    finally:
        cleanup()

if __name__ == "__main__":
    benchmark()
