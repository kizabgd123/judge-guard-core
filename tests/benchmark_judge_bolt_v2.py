import time
import os
import sys
import subprocess
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

def benchmark_import():
    # We use a subprocess to measure cold import time accurately
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    cmd = [sys.executable, "-c", "import time; start = time.perf_counter(); import judge_guard; print((time.perf_counter() - start) * 1000)"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        return float(result.stdout.strip())
    else:
        print(f"Import benchmark failed: {result.stderr}")
        return 0.0

def benchmark_init_and_cached_verify():
    # Setup test WORK_LOG.md
    with open("WORK_LOG.md", "w") as f:
        f.write("🟡 Starting Benchmark Action\n")

    # Mock dependencies to focus on JudgeGuard's own logic overhead
    # We want to measure the "fast path" (cached hit)
    with patch('src.antigravity_core.mobile_bridge.bridge.push_verdict'), \
         patch('research_pipeline.ResearchPipeline.connect') as mock_connect:

        mock_pipeline = MagicMock()
        mock_connect.return_value = mock_pipeline
        mock_pipeline.get_cached_verdict.return_value = "PASSED"

        # We need to reload judge_guard if it was already imported
        if 'judge_guard' in sys.modules:
            import importlib
            importlib.reload(sys.modules['judge_guard'])
        import judge_guard
        from judge_guard import JudgeGuard

        # Measure Init
        start = time.perf_counter()
        guard = JudgeGuard()
        init_time = (time.perf_counter() - start) * 1000

        # Measure Cached Verify
        action = "Benchmark Action"
        start = time.perf_counter()
        res = guard.verify_action(action)
        verify_time = (time.perf_counter() - start) * 1000

        return init_time, verify_time

if __name__ == "__main__":
    print("--- ⚡ JudgeGuard Performance Baseline ---")

    import_ms = benchmark_import()
    print(f"Cold Import Time: {import_ms:.2f} ms")

    init_ms, verify_ms = benchmark_init_and_cached_verify()
    print(f"Initialization Time: {init_ms:.2f} ms")
    print(f"Cached Verification (Fast Path): {verify_ms:.2f} ms")
    print(f"Total Startup + Verify: {import_ms + init_ms + verify_ms:.2f} ms")
