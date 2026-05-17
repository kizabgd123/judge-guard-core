
import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

# Create a temporary WORK_LOG.md
WORK_LOG_PATH = "BENCHMARK_WORK_LOG.md"

def setup():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting test action\n")

def teardown():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)

def benchmark():
    from judge_guard import JudgeGuard

    # Mock evaluate and other things to isolate non-AI overhead
    with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True), \
         patch('src.antigravity_core.mobile_bridge.bridge.push_verdict'), \
         patch('research_pipeline.ResearchPipeline.get_cached_verdict', return_value="PASSED"):

        guard = JudgeGuard(work_log_path=WORK_LOG_PATH)

        # Warm up
        guard.verify_action("Test Action")

        start = time.time()
        for _ in range(100):
            # Update mtime to simulate new log entry if needed,
            # though here we are testing cache hit in ResearchPipeline
            guard.verify_action("Test Action")
        end = time.time()

        print(f"Average verify_action (cached hit) latency: {(end - start) / 100 * 1000:.4f}ms")

if __name__ == "__main__":
    setup()
    try:
        benchmark()
    finally:
        teardown()
