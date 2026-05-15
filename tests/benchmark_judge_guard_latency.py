import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies to avoid import errors and network calls
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Now we can import things
import src.antigravity_core.judge_flow
import src.antigravity_core.gemini_client
import src.antigravity_core.mobile_bridge

# Create a temporary WORK_LOG.md for testing
WORK_LOG_PATH = "TEST_LATENCY_WORK_LOG.md"

def setup_test_env():
    # Create a reasonably sized log file to simulate real usage
    with open(WORK_LOG_PATH, "w") as f:
        for i in range(100):
            f.write(f"Log entry {i}: Some activity recorded here.\n")
        f.write("🟡 Starting Latency Benchmark Action\n")

def cleanup_test_env():
    if os.path.exists(WORK_LOG_PATH):
        os.remove(WORK_LOG_PATH)
    if os.path.exists("research.db"):
        os.remove("research.db")

def run_benchmark():
    # Mocking dependencies to have ZERO latency for AI parts
    with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True), \
         patch('src.antigravity_core.gemini_client.GeminiClient.judge_content', return_value=True), \
         patch('src.antigravity_core.mobile_bridge.bridge.push_verdict'), \
         patch('judge_guard.load_dotenv'):

        from judge_guard import JudgeGuard

        # Initialize JudgeGuard
        guard = JudgeGuard(work_log_path=WORK_LOG_PATH)

        action = "Latency Benchmark Action"

        print(f"\n--- Measuring JudgeGuard.verify_action Overhead (AI mocked to 0ms) ---")

        # 1. First call (Cache Miss)
        # We need to make sure it's not in cache
        if guard.pipeline:
             with guard.pipeline.conn:
                 guard.pipeline.conn.execute("DELETE FROM verdicts")

        start = time.time()
        guard.verify_action(action)
        end = time.time()
        miss_latency = (end - start) * 1000
        print(f"Cache MISS Latency (Overhead): {miss_latency:.4f}ms")

        # 2. Second call (Cache Hit)
        start = time.time()
        guard.verify_action(action)
        end = time.time()
        hit_latency = (end - start) * 1000
        print(f"Cache HIT Latency (Overhead): {hit_latency:.4f}ms")

        # Run multiple times to get average
        iterations = 100

        # Measure Hit Latency average
        total_hit_time = 0
        for _ in range(iterations):
            start = time.time()
            guard.verify_action(action)
            end = time.time()
            total_hit_time += (end - start)

        avg_hit_latency = (total_hit_time / iterations) * 1000
        print(f"Average Cache HIT Latency ({iterations} runs): {avg_hit_latency:.4f}ms")

if __name__ == "__main__":
    setup_test_env()
    try:
        run_benchmark()
    finally:
        cleanup_test_env()
