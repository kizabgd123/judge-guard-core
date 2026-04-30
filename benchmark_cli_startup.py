import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Create a temporary WORK_LOG.md for testing
WORK_LOG_PATH = "TEST_WORK_LOG.md"
DB_PATH = "research.db"

def setup_test_env():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Benchmark Action\n")

    # Correctly initialize the ResearchPipeline database
    from research_pipeline import ResearchPipeline
    pipeline = ResearchPipeline()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    pipeline.init_db()
    # Pre-populate a verdict for cache hit measurement
    pipeline.cache_verdict("Benchmarked Action", "PASSED")
    pipeline.close()

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)

def measure_startup():
    print("\n--- Measuring JudgeGuard Initialization & Cache Hit (Optimized) ---")

    # Measure import time
    start = time.time()
    import judge_guard
    from judge_guard import JudgeGuard
    mid = time.time()
    print(f"Import time: {mid - start:.4f}s")

    # Measure initialization time (should be very fast now)
    start = time.time()
    guard = JudgeGuard(work_log_path=WORK_LOG_PATH)
    end = time.time()
    print(f"Initialization time: {end - start:.4f}s")

    # Measure cache hit duration
    action = "Benchmarked Action"
    start = time.time()
    res = guard.verify_action(action)
    end = time.time()
    print(f"Cache Hit (verify_action) duration: {end - start:.4f}s (Result: {res})")

    # Verify properties are indeed lazy
    print("\nAccessing lazy properties...")
    start = time.time()
    _ = guard.brain_path
    end = time.time()
    print(f"First brain_path access: {end - start:.4f}s")

    start = time.time()
    _ = guard.immutable_laws
    end = time.time()
    print(f"First immutable_laws access: {end - start:.4f}s")

    return end - start

if __name__ == "__main__":
    setup_test_env()
    try:
        measure_startup()
    finally:
        cleanup_test_env()
