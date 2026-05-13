import os
import unittest
import sys
from unittest.mock import MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

from judge_guard import JudgeGuard

class TestJudgeGuardCaching(unittest.TestCase):
    def setUp(self):
        self.work_log_path = "TEST_CACHING_WORK_LOG.md"
        with open(self.work_log_path, "w") as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        self.guard = JudgeGuard(work_log_path=self.work_log_path)

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def test_cache_poisoning_fix(self):
        # 1. First call with small max_chars
        context1 = self.guard._load_context(max_chars=10)
        self.assertEqual(len(context1), 10)

        # 2. Second call with larger max_chars (should NOT be poisoned by context1)
        context2 = self.guard._load_context(max_chars=20)
        self.assertEqual(len(context2), 20)

        # 3. Third call with smaller max_chars (should be served from cache)
        # We can't easily prove it's from cache without mocking os.path.getmtime or open
        # but we can verify it returns correct data.
        context3 = self.guard._load_context(max_chars=5)
        self.assertEqual(len(context3), 5)
        self.assertEqual(context3, "ne 5\n")

    def test_cache_invalidation_on_mtime_change(self):
        # 1. Load context
        context1 = self.guard._load_context(max_chars=100)

        # 2. Modify file
        import time
        time.sleep(0.1) # Ensure mtime changes
        with open(self.work_log_path, "a") as f:
            f.write("Line 6\n")

        # 3. Load context again (should detect change and read new content)
        context2 = self.guard._load_context(max_chars=100)
        self.assertIn("Line 6", context2)
        self.assertNotEqual(context1, context2)

if __name__ == "__main__":
    unittest.main()
