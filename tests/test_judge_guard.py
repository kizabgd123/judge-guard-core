import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from judge_guard import JudgeGuard

class TestJudgeGuard(unittest.TestCase):
    def setUp(self):
        self.brain_path = "/tmp/test_brain"
        self.work_log_path = "/tmp/test_work_log.md"
        
        # Create dummy work log
        with open(self.work_log_path, "w") as f:
            f.write("Log Entry 1\nLog Entry 2")
            
        self.judge = JudgeGuard(brain_path=self.brain_path, work_log_path=self.work_log_path)

    @patch('src.antigravity_core.judge_flow.BlockJudge.evaluate')
    def test_verify_action_pass(self, mock_evaluate):
        # Mock the BlockJudge to return True (PASSED)
        mock_evaluate.return_value = True
        
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
        self.assertIn("Log Entry 1", context)

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

if __name__ == '__main__':
    unittest.main()
