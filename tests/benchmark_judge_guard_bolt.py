import time
import os
import sys
from unittest.mock import MagicMock

# Add current dir to path to import local modules
sys.path.append(os.getcwd())

def benchmark_judge_guard():
    # Mock bridge BEFORE importing judge_guard
    mock_bridge = MagicMock()
    sys.modules['src.antigravity_core.mobile_bridge'] = MagicMock(bridge=mock_bridge)

    from judge_guard import JudgeGuard
    from research_pipeline import ResearchPipeline

    # Setup test environment
    if os.path.exists("research.db"):
        os.remove("research.db")

    with open("WORK_LOG.md", "w") as f:
        f.write("🟡 Starting test action")

    # Ensure DB exists
    rp = ResearchPipeline().init_db()
    action = "test action"
    rp.cache_verdict(action, "PASSED")
    rp.close()

    start_init = time.perf_counter()
    guard = JudgeGuard()
    init_time = time.perf_counter() - start_init

    # Warm up (trigger lazy loading)
    guard.verify_action(action)

    # Measure cached hit
    start = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        guard.verify_action(action)
    duration = (time.perf_counter() - start) / iterations

    print(f"Init time: {init_time*1000:.4f}ms")
    print(f"Cached verify_action duration: {duration*1000:.4f}ms")

if __name__ == "__main__":
    benchmark_judge_guard()
