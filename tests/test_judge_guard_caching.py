import os
import time
import sys
from unittest.mock import MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

from judge_guard import JudgeGuard

WORK_LOG_PATH = "TEST_CACHE_WORK_LOG.md"

def test_caching():
    # Setup
    with open(WORK_LOG_PATH, "w") as f:
        f.write("🟡 Starting Action 1\n")

    guard = JudgeGuard(work_log_path=WORK_LOG_PATH)

    # 1. Initial check (should cache)
    assert guard._check_work_log("Action 1") == True
    first_lines = guard._log_cache["content"]
    assert "action 1" in first_lines

    # 2. Check again without change (should hit cache)
    assert guard._check_work_log("Action 1") == True
    assert guard._log_cache["content"] is first_lines # Same object/content

    # 3. Modify file (should invalidate cache)
    time.sleep(0.1) # Ensure mtime changes if granularity is low
    with open(WORK_LOG_PATH, "a") as f:
        f.write("🟡 Starting Action 2\n")

    assert guard._check_work_log("Action 2") == True
    assert "action 2" in guard._log_cache["content"]
    assert guard._log_cache["content"] != first_lines

if __name__ == "__main__":
    try:
        test_caching()
        print("✅ Caching verification test passed!")
    finally:
        if os.path.exists(WORK_LOG_PATH):
            os.remove(WORK_LOG_PATH)
