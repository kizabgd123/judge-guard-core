import time
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# We'll measure the REAL import time first
def measure_real_import():
    start = time.time()
    import judge_guard
    import importlib
    importlib.reload(judge_guard)
    end = time.time()
    return (end - start)

def run_benchmarks():
    print("--- JudgeGuard Performance Baseline ---")

    import judge_guard
    from judge_guard import JudgeGuard

    # 1. Initialization latency
    start = time.time()
    for _ in range(100):
        guard = JudgeGuard()
    end = time.time()
    avg_init = (end - start) / 100 * 1000
    print(f"Average Initialization: {avg_init:.4f}ms")

    # 2. Hot-path (Cache Hit) latency
    # Mocking pipeline for consistent cache hit
    mock_pipeline = MagicMock()
    mock_pipeline.get_cached_verdict.return_value = "PASSED"

    # Mocking work log
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write("🟡 Starting baseline test\n")
        work_log_path = tf.name

    try:
        guard = JudgeGuard(work_log_path=work_log_path)
        guard._pipeline = mock_pipeline # Inject mock

        action = "Baseline cached action"

        # Warm up
        guard.verify_action(action)

        start = time.time()
        iterations = 1000
        for _ in range(iterations):
            guard.verify_action(action)
        end = time.time()
        avg_hotpath = (end - start) / iterations * 1000
        print(f"Average Cache Hit (verify_action): {avg_hotpath:.4f}ms")

    finally:
        if os.path.exists(work_log_path):
            os.remove(work_log_path)

if __name__ == "__main__":
    import_time = measure_real_import()
    print(f"Import Latency (judge_guard): {import_time * 1000:.2f}ms")
    run_benchmarks()
