import time
import os
import sys
import hashlib
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Create a temporary WORK_LOG.md for testing
WORK_LOG_PATH = "HOTPATH_WORK_LOG.md"
DB_PATH = "research.db"

def setup_test_env():
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Hotpath Action\n")

    # Initialize ResearchPipeline and seed cache
    from research_pipeline import ResearchPipeline
    rp = ResearchPipeline().init_db()
    rp.cache_verdict("Hotpath Action", "PASSED")
    rp.close()

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def run_benchmark():
    from judge_guard import JudgeGuard

    # We want to measure the "hot path" which includes:
    # 1. _check_work_log (disk I/O)
    # 2. pipeline.get_cached_verdict (SQLite I/O)
    # 3. _is_research_action (CPU)

    # We mock the bridge to avoid network/print overhead
    with patch('src.antigravity_core.mobile_bridge.bridge.push_verdict'):
        guard = JudgeGuard(work_log_path=WORK_LOG_PATH)
        action = "Hotpath Action"

        print(f"\n--- Benchmarking JudgeGuard.verify_action Hot-Path (Cached Hit) ---")

        # Warm up
        guard.verify_action(action)

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            guard.verify_action(action)
        end = time.perf_counter()

        avg_latency = (end - start) / iterations * 1000
        print(f"Average Hot-Path Latency: {avg_latency:.4f}ms ({iterations} iterations)")

if __name__ == "__main__":
    setup_test_env()
    try:
        run_benchmark()
    finally:
        cleanup_test_env()
