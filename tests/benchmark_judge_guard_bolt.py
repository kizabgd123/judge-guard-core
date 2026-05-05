import time
import os
import sys
import subprocess
import hashlib

# Ensure project root is in path
sys.path.append(os.getcwd())

def measure_import():
    # Use a separate process to measure cold import time
    start = time.time()
    subprocess.run([sys.executable, "-c", "import judge_guard"], capture_output=True)
    return (time.time() - start) * 1000

def setup_work_log():
    with open("WORK_LOG.md", "a") as f:
        f.write("🟡 Starting Benchmark Action\n")

def run_benchmarks():
    import judge_guard
    from judge_guard import JudgeGuard

    # 1. Initialization time
    start = time.time()
    guard = JudgeGuard()
    init_time = (time.time() - start) * 1000

    # 2. Cached verification latency
    action = "Benchmarked Action"

    # We need to manually inject a cached verdict into the DB to measure the "fast path"
    if guard.pipeline:
        guard.pipeline.cache_verdict(action, "PASSED")

    # Ensure work log is fresh
    setup_work_log()

    # Measure cached hit
    latencies = []
    for _ in range(100):
        start = time.time()
        guard.verify_action(action)
        latencies.append((time.time() - start) * 1000)

    avg_cached_latency = sum(latencies) / len(latencies)

    return init_time, avg_cached_latency

if __name__ == "__main__":
    # Create empty research.db if it doesn't exist
    if not os.path.exists("research.db"):
        from research_pipeline import ResearchPipeline
        ResearchPipeline().init_db().close()

    cold_import = measure_import()
    init_t, cached_lat = run_benchmarks()

    print(f"--- JudgeGuard Baseline Benchmarks ---")
    print(f"Cold Import Time: {cold_import:.2f} ms")
    print(f"Initialization Time: {init_t:.2f} ms")
    print(f"Cached Verification (Fast Path): {cached_lat:.4f} ms")
