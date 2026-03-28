import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock GeminiClient and bridge before importing JudgeGuard to avoid environment issues during init
with patch('src.antigravity_core.gemini_client.GeminiClient'), \
     patch('src.antigravity_core.mobile_bridge.bridge'):
    from judge_guard import JudgeGuard

class TestJudgeGuard(unittest.TestCase):
    def setUp(self):
        self.work_log_path = "/tmp/test_work_log.md"
        
        # Create dummy work log that meets the requirements
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")
            
        # Patch dependencies for the JudgeGuard instance
        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', True), \
             patch('src.antigravity_core.gemini_client.GeminiClient'), \
             patch('src.antigravity_core.mobile_bridge.bridge'):
            self.judge = JudgeGuard(work_log_path=self.work_log_path)

    @patch('src.antigravity_core.judge_flow.BlockJudge.evaluate')
    def test_verify_action_pass(self, mock_evaluate):
        # Mock the BlockJudge to return True (PASSED)
        mock_evaluate.return_value = True
        
        # We need to make sure _check_work_log passes
        verdict = self.judge.verify_action("Valid Action")
        self.assertTrue(verdict)

    @patch('src.antigravity_core.judge_flow.BlockJudge.evaluate')
    def test_verify_action_block(self, mock_evaluate):
        # Mock the BlockJudge to return False (BLOCKED)
        mock_evaluate.return_value = False
        
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
