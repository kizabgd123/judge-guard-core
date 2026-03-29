import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock GeminiClient, bridge, and judge_flow before importing JudgeGuard to avoid
# environment-dependent initialization during import
mock_judge_flow = MagicMock()
sys.modules.setdefault('src.antigravity_core.gemini_client', MagicMock())
sys.modules.setdefault('src.antigravity_core.mobile_bridge', MagicMock())
sys.modules.setdefault('src.antigravity_core.judge_flow', mock_judge_flow)

from judge_guard import JudgeGuard

class TestJudgeGuard(unittest.TestCase):
    def setUp(self):
        self.work_log_path = "/tmp/test_work_log.md"

        # Create dummy work log that meets the requirements
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")

        # Patch dependencies for the JudgeGuard instance
        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', True):
            self.judge = JudgeGuard(work_log_path=self.work_log_path)

    @patch('judge_guard.JudgeGuard._check_work_log')
    def test_verify_action_pass(self, mock_check_log):
        # Mock the BlockJudge to return True (PASSED)
        mock_judge_flow.BlockJudge.return_value.evaluate.return_value = True
        mock_check_log.return_value = True

        # We need to make sure _check_work_log passes
        verdict = self.judge.verify_action("Valid Action")
        self.assertTrue(verdict)

    @patch('judge_guard.JudgeGuard._check_work_log')
    def test_verify_action_block(self, mock_check_log):
        # Mock the BlockJudge to return False (BLOCKED)
        mock_judge_flow.BlockJudge.return_value.evaluate.return_value = False
        mock_check_log.return_value = True

        verdict = self.judge.verify_action("Malicious Action")
        self.assertFalse(verdict)

    def test_load_context(self):
        context = self.judge._load_context()
        self.assertIn("Starting Valid Action", context)

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

if __name__ == '__main__':
    unittest.main()