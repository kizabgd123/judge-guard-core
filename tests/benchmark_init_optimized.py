import time
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock dependencies that are not needed for init
sys.modules['src.antigravity_core.gemini_client'] = MagicMock()
sys.modules['research_pipeline'] = MagicMock()
sys.modules['src.antigravity_core.mobile_bridge'] = MagicMock()

from judge_guard import JudgeGuard

def benchmark_init():
    iterations = 1000
    start = time.time()
    for _ in range(iterations):
        # We need to make sure we don't hit the filesystem too hard if it's slow,
        # but here we want to measure the overhead.
        guard = JudgeGuard()
    end = time.time()
    avg_time = (end - start) / iterations
    print(f"Average JudgeGuard.__init__ time: {avg_time*1000:.4f}ms")

if __name__ == "__main__":
    # Create dummy MASTER_ORCHESTRATION.md if it doesn't exist
    rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    if not os.path.exists(rules_path):
        with open(rules_path, "w") as f:
            f.write("# Dummy Rules\n" * 100) # Some content

    benchmark_init()
