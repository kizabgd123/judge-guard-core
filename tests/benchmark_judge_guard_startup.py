import time
import os
import sys
import subprocess
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock heavy dependencies for the in-process parts of the benchmark
# to ensure we measure the JudgeGuard logic overhead, not the mock library overhead.
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

WORK_LOG_PATH = "BENCHMARK_WORK_LOG.md"

def setup_test_env():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Benchmark Action\n")
    # Pre-warm the cache in research.db if it exists, or create it
    from research_pipeline import ResearchPipeline
    rp = ResearchPipeline()
    if not os.path.exists("research.db"):
        rp.init_db()
    else:
        rp.connect()
    rp.cache_verdict("Benchmarked Action", "PASSED")
    rp.close()

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)
    # We keep research.db for the benchmark but could remove it if we want a clean state
    # if os.path.exists("research.db"):
    #    os.remove("research.db")

def measure_cold_import():
    # Measure how long it takes to just 'import judge_guard' in a new process
    start = time.time()
    subprocess.run([sys.executable, "-c", "import judge_guard"], check=True)
    return time.time() - start

def run_benchmarks():
    print("--- JudgeGuard Performance Baseline ---")

    # 1. Cold Import Time
    import_times = []
    for _ in range(5):
        import_times.append(measure_cold_import())
    print(f"Cold Import Time: {sum(import_times)/len(import_times):.4f}s")

    # 2. Initialization & Cached Verification
    from judge_guard import JudgeGuard

    # Measure initialization
    start_init = time.time()
    guard = JudgeGuard(work_log_path=WORK_LOG_PATH)
    end_init = time.time()
    print(f"Initialization Time: {(end_init - start_init)*1000:.4f}ms")

    # Measure Cached Verification (Hot Path)
    # This assumes research.db has the verdict cached
    iterations = 100
    start_cache = time.time()
    for _ in range(iterations):
        # We don't update utime here because we want to measure the fastest possible path
        # (even if it might be stale in a real scenario, we want the overhead)
        guard.verify_action("Benchmarked Action")
    end_cache = time.time()
    print(f"Cached Verification (Hot Path) Average: {(end_cache - start_cache)/iterations*1000:.4f}ms")

if __name__ == "__main__":
    setup_test_env()
    try:
        run_benchmarks()
    finally:
        cleanup_test_env()
