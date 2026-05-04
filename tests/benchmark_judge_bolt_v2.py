import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

def run_benchmark():
    # 1. Measure Cold Import Time
    # Use a subprocess to ensure a fresh environment for cold import
    import subprocess
    cmd = [sys.executable, "-c", "import time; s=time.perf_counter(); import judge_guard; print((time.perf_counter()-s)*1000)"]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "."})
    cold_import_ms = float(result.stdout.strip())

    # 2. Measure Initialization Time
    import judge_guard
    start = time.perf_counter()
    guard = judge_guard.JudgeGuard()
    init_ms = (time.perf_counter() - start) * 1000

    # 3. Measure Cached Verification Latency
    # Create a dummy WORK_LOG.md
    with open("WORK_LOG.md", "w") as f:
        f.write("🟡 Starting test\n")

    # Mock pipeline to return a cached verdict
    mock_pipeline = MagicMock()
    mock_pipeline.get_cached_verdict.return_value = "PASSED"
    guard._pipeline = mock_pipeline

    # Mock bridge to avoid disk I/O there during benchmark
    with patch('src.antigravity_core.mobile_bridge.bridge.push_verdict'):
        # Warm up
        guard.verify_action("test action")

        start = time.perf_counter()
        for _ in range(100):
            guard.verify_action("test action")
        avg_cached_ms = (time.perf_counter() - start) * 10 / 100 # average for 1 call

    print(f"Cold Import: {cold_import_ms:.2f}ms")
    print(f"Initialization: {init_ms:.2f}ms")
    print(f"Cached Verification: {avg_cached_ms:.4f}ms")

if __name__ == "__main__":
    run_benchmark()
