import os
import time
from unittest.mock import patch, MagicMock
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

# Create a more robust mock environment for JudgeGuard
mock_gemini = MagicMock()
mock_bridge = MagicMock()

# Mocking modules before import
sys.modules['src.antigravity_core.gemini_client'] = MagicMock()
sys.modules['src.antigravity_core.mobile_bridge'] = MagicMock()
sys.modules['src.antigravity_core.judge_flow'] = MagicMock()

import judge_guard

def generate_large_log(filepath, size_mb=10):
    """Generates a large WORK_LOG.md for testing."""
    line = "## 2026-01-16 - Some standard log entry that takes up space\n"
    target_bytes = int(size_mb * 1024 * 1024)
    with open(filepath, "w") as f:
        current_bytes = 0
        while current_bytes < target_bytes:
            f.write(line)
            current_bytes += len(line)
        f.write("🟡 Starting Final Benchmark Action\n")

def run_benchmark():
    log_path = "LARGE_WORK_LOG.md"
    generate_large_log(log_path, size_mb=10)

    # Initialize JudgeGuard with the large log
    # We need to manually set some attributes since we bypassed real initialization
    guard = judge_guard.JudgeGuard(work_log_path=log_path)

    print(f"--- Benchmarking Log Retrieval (Log Size: {os.path.getsize(log_path) / (1024*1024):.2f} MB) ---")

    # Measure _load_context
    start = time.time()
    for _ in range(10):
        guard._load_context(max_chars=15000)
    end = time.time()
    print(f"_load_context (10 iterations): {end - start:.4f}s")

    # Measure _check_work_log
    start = time.time()
    for _ in range(10):
        guard._check_work_log("Final Benchmark Action")
    end = time.time()
    print(f"_check_work_log (10 iterations): {end - start:.4f}s")

    # Cleanup
    if os.path.exists(log_path):
        os.remove(log_path)

if __name__ == "__main__":
    run_benchmark()
