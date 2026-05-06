import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies to avoid real I/O or AI calls during measurement of logic overhead
sys.modules['src.antigravity_core.mobile_bridge'] = MagicMock()

def run_startup_benchmark():
    from judge_guard import JudgeGuard

    print("\n--- JudgeGuard Startup & Fast-Path Benchmark ---")

    # Measure cold import (sort of, it's already imported but let's see)
    start = time.time()
    guard = JudgeGuard()
    end = time.time()
    print(f"Initialization time: {(end - start) * 1000:.2f}ms")

    # Mock WORK_LOG.md for _check_work_log
    with open("WORK_LOG.md", "w") as f:
        f.write("🟡 Starting action\n")

    # 1. Measure verify_action (CACHED hit)
    mock_pipeline = MagicMock()
    mock_pipeline.get_cached_verdict.return_value = "PASSED"
    guard._pipeline = mock_pipeline

    start = time.time()
    for _ in range(100):
        guard.verify_action("Some cached action")
    end = time.time()
    print(f"Cached verify_action (100 calls) avg: {(end - start) * 10:.4f}ms")

    # 2. Measure verify_action (NON-CACHED path, but LLM mocked)
    # This will exercise _check_work_log, _load_context, _detect_phase, etc.
    mock_pipeline.get_cached_verdict.return_value = None

    # Mock LLM and other properties
    guard._gemini = MagicMock()
    with patch('src.antigravity_core.judge_flow.BlockJudge') as mock_judge_class:
        mock_judge_instance = mock_judge_class.return_value
        mock_judge_instance.evaluate.return_value = True

        start = time.time()
        for _ in range(100):
            guard.verify_action("Some new action")
        end = time.time()
        print(f"Non-cached verify_action (100 calls) avg: {(end - start) * 10:.4f}ms")

    # Cleanup
    if os.path.exists("WORK_LOG.md"):
        os.remove("WORK_LOG.md")

if __name__ == "__main__":
    run_startup_benchmark()
