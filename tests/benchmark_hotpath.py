
import time
import os
import sys
import hashlib
from judge_guard import JudgeGuard

def setup_env():
    # 1. Create dummy WORK_LOG.md
    with open("WORK_LOG.md", "w") as f:
        f.write("🟡 Starting benchmark action\n")

    # 2. Setup ResearchPipeline with cached verdict
    from research_pipeline import ResearchPipeline
    pipeline = ResearchPipeline()
    if os.path.exists("research.db"):
        os.remove("research.db")
    pipeline.init_db()

    action = "benchmark action"
    pipeline.cache_verdict(action, "PASSED")
    pipeline.close()

def benchmark():
    # Measure import + init + verify
    start_total = time.perf_counter()

    # Init
    start_init = time.perf_counter()
    guard = JudgeGuard()
    end_init = time.perf_counter()

    # Verify (Hot path: cached)
    action = "benchmark action"
    start_verify = time.perf_counter()
    passed = guard.verify_action(action)
    end_verify = time.perf_counter()

    end_total = time.perf_counter()

    print(f"Init latency: {(end_init - start_init) * 1000:.3f} ms")
    print(f"Verify latency (cached): {(end_verify - start_verify) * 1000:.3f} ms")
    print(f"Total turnaround: {(end_total - start_total) * 1000:.3f} ms")

    if not passed:
        print("Error: Verification failed!")
        sys.exit(1)

if __name__ == "__main__":
    setup_env()
    # Run once to warm up (imports etc are already done in this process)
    # But JudgeGuard is initialized twice here for better measurement
    print("--- Benchmark ---")
    benchmark()
