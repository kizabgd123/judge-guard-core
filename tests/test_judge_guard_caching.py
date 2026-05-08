import unittest
import os
import time
from judge_guard import JudgeGuard

class TestJudgeGuardCaching(unittest.TestCase):
    def setUp(self):
        self.log_path = "TEST_CACHE_LOG.md"
        with open(self.log_path, "w") as f:
            f.write("Line 1\nLine 2\n")
        self.guard = JudgeGuard(work_log_path=self.log_path)

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_caching_logic(self):
        # First read - should populate cache
        context1 = self.guard._get_log_context(100)
        self.assertIn("Line 2", context1)
        self.assertEqual(self.guard._log_cache["size_read"], len(context1.encode()))

        # Second read - should use cache (we can't easily see if it used cache
        # without mocking open, but we can check if mtime matches)
        mtime1 = os.path.getmtime(self.log_path)
        self.assertEqual(self.guard._log_cache["mtime"], mtime1)

        context2 = self.guard._get_log_context(100)
        self.assertEqual(context1, context2)

        # Modify file - should invalidate cache
        time.sleep(0.1) # Ensure mtime changes
        with open(self.log_path, "a") as f:
            f.write("Line 3\n")

        mtime2 = os.path.getmtime(self.log_path)
        self.assertNotEqual(mtime1, mtime2)

        context3 = self.guard._get_log_context(100)
        self.assertIn("Line 3", context3)
        self.assertEqual(self.guard._log_cache["mtime"], mtime2)

    def test_cache_size_handling(self):
        # Read small amount
        self.guard._get_log_context(5)
        self.assertEqual(self.guard._log_cache["size_read"], 5)

        # Read larger amount - should trigger re-read if cache is too small
        self.guard._get_log_context(20)
        self.assertEqual(self.guard._log_cache["size_read"], len("Line 1\nLine 2\n".encode()))

if __name__ == "__main__":
    unittest.main()
