import time
import os
import sys
from unittest.mock import patch, MagicMock

# Mock GeminiClient and bridge before importing JudgeGuard
with patch('src.antigravity_core.gemini_client.GeminiClient'), \
     patch('src.antigravity_core.mobile_bridge.bridge'):
    from judge_guard import JudgeGuard

BENCHMARK_LOG = "BENCHMARK_WORK_LOG.md"

def setup_large_log(size_mb=10):
    print(f"Generating {size_mb}MB log file...")
    with open(BENCHMARK_LOG, "w") as f:
        f.write("Some initial content\n")
        # Write large amount of filler
        filler = "This is a line of filler content to increase the file size.\n" * 1000
        for _ in range(size_mb * 18): # Roughly 10MB
            f.write(filler)
        f.write("🟡 Starting Benchmark Action\n")

def run_benchmark(iterations=100):
    # Patch dependencies for the JudgeGuard instance
    with patch('judge_guard.JUDGE_AVAILABLE', True), \
         patch('judge_guard.BRIDGE_AVAILABLE', True), \
         patch('src.antigravity_core.gemini_client.GeminiClient'), \
         patch('src.antigravity_core.mobile_bridge.bridge'):

        guard = JudgeGuard(work_log_path=BENCHMARK_LOG)

        print(f"Running benchmark for {iterations} iterations...")

        # Benchmark _load_context
        start_time = time.time()
        for _ in range(iterations):
            guard._load_context()
        load_context_duration = time.time() - start_time
        print(f"_load_context avg: {load_context_duration / iterations:.6f}s (Total: {load_context_duration:.4f}s)")

        # Benchmark _check_work_log
        start_time = time.time()
        for _ in range(iterations):
            guard._check_work_log("Benchmark Action")
        check_log_duration = time.time() - start_time
        print(f"_check_work_log avg: {check_log_duration / iterations:.6f}s (Total: {check_log_duration:.4f}s)")

        return load_context_duration, check_log_duration

if __name__ == "__main__":
    try:
        setup_large_log(10)
        run_benchmark(100)
    finally:
        if os.path.exists(BENCHMARK_LOG):
            os.remove(BENCHMARK_LOG)
