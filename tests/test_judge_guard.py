import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

with patch('src.antigravity_core.gemini_client.genai'), patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
    from judge_guard import JudgeGuard

class TestJudgeGuard(unittest.TestCase):
    @patch('src.antigravity_core.gemini_client.genai')
    def setUp(self, mock_genai):
        self.brain_path = "/tmp/test_brain"
        self.work_log_path = "/tmp/test_work_log.md"
        
        # Create dummy work log
        with open(self.work_log_path, "w") as f:
            f.write("Log Entry 1\nLog Entry 2")
            
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            self.judge = JudgeGuard(brain_path=self.brain_path, work_log_path=self.work_log_path)

    @patch('src.antigravity_core.judge_flow.BlockJudge.evaluate')
    @patch('judge_guard.JudgeGuard._check_work_log')
    @patch('src.antigravity_core.judge_flow.GeminiClient')
    def test_verify_action_pass(self, mock_gemini, mock_check_log, mock_evaluate):
        # Mock the BlockJudge to return True (PASSED)
        mock_evaluate.return_value = True
        mock_check_log.return_value = True
        
        verdict = self.judge.verify_action("Valid Action")
        self.assertTrue(verdict)

    @patch('src.antigravity_core.judge_flow.BlockJudge.evaluate')
    @patch('judge_guard.JudgeGuard._check_work_log')
    @patch('src.antigravity_core.judge_flow.GeminiClient')
    def test_verify_action_block(self, mock_gemini, mock_check_log, mock_evaluate):
        # Mock the BlockJudge to return False (BLOCKED)
        mock_evaluate.return_value = False
        mock_check_log.return_value = True
        
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
