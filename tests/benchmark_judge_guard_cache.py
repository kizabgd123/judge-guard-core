import time
import os
import logging
from judge_guard import JudgeGuard

# Configure logging to see Bolt info
logging.basicConfig(level=logging.INFO)

def benchmark():
    guard = JudgeGuard()
    action = "test: run pytest tests/test_judge_guard.py"
    dangerous_action = "sudo rm -rf /"

    # Ensure WORK_LOG.md has the entry to pass Layer 0
    with open("WORK_LOG.md", "a") as f:
        f.write(f"\n🟡 Starting {action}\n")

    print(f"\n>>> Benchmarking regular action: {action}")

    start = time.time()
    guard.verify_action(action)
    end = time.time()
    print(f"First run (should be LLM/Mock): {end - start:.4f}s")

    start = time.time()
    guard.verify_action(action)
    end = time.time()
    print(f"Second run (should be CACHE): {end - start:.4f}s")

    print(f"\n>>> Benchmarking dangerous action: {dangerous_action}")
    # Even if we "force" it into cache (which we shouldn't be able to easily)
    # the security check should catch it first.

    start = time.time()
    result = guard.verify_action(dangerous_action)
    end = time.time()
    print(f"Dangerous action result: {result} (expected: False)")
    print(f"Dangerous action check took: {end - start:.4f}s")

if __name__ == "__main__":
    benchmark()
