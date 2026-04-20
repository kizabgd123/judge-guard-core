import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import os
import sys

# Mock dependencies to avoid import errors in some environments
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Now we can import things
import src.antigravity_core.judge_flow
import src.antigravity_core.gemini_client
import src.antigravity_core.mobile_bridge

from judge_guard import JudgeGuard

class TestJudgeGuard(unittest.TestCase):
    def setUp(self):
        """
        Prepare test fixture by creating a dummy work log and instantiating a JudgeGuard with patched dependencies.
        
        Creates a temporary work log at /tmp/test_work_log.md containing the marker "🟡 Starting Valid Action", and patches module-level availability flags and external clients so that a JudgeGuard can be constructed with work_log_path pointing to the created file.
        """
        self.work_log_path = "/tmp/test_work_log_md"
        
        # Create dummy work log that meets the requirements
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")
            
        # Instantiate JudgeGuard
        self.judge = JudgeGuard(work_log_path=self.work_log_path)

    @patch('judge_guard.JudgeGuard.gemini', new_callable=PropertyMock)
    @patch('judge_guard.JudgeGuard.block_judge_class', new_callable=PropertyMock)
    @patch('judge_guard.JudgeGuard.bridge', new_callable=PropertyMock)
    def test_verify_action_pass(self, mock_bridge, mock_block_judge_class, mock_gemini):
        # Mock dependencies
        mock_gemini.return_value = MagicMock()
        mock_judge_instance = MagicMock()
        mock_judge_instance.evaluate.return_value = True
        mock_block_judge_class.return_value = MagicMock(return_value=mock_judge_instance)
        mock_bridge.return_value = MagicMock()
        
        # We need to make sure _check_work_log passes
        verdict = self.judge.verify_action("Valid Action")
        self.assertTrue(verdict)

    @patch('judge_guard.JudgeGuard.gemini', new_callable=PropertyMock)
    @patch('judge_guard.JudgeGuard.block_judge_class', new_callable=PropertyMock)
    @patch('judge_guard.JudgeGuard.bridge', new_callable=PropertyMock)
    def test_verify_action_block(self, mock_bridge, mock_block_judge_class, mock_gemini):
        # Mock dependencies
        mock_gemini.return_value = MagicMock()
        mock_judge_instance = MagicMock()
        mock_judge_instance.evaluate.return_value = False
        mock_block_judge_class.return_value = MagicMock(return_value=mock_judge_instance)
        mock_bridge.return_value = MagicMock()
        
        verdict = self.judge.verify_action("Malicious Action")
        self.assertFalse(verdict)

    def test_load_context(self):
        context = self.judge._load_context()
        self.assertIn("Starting Valid Action", context)

    def tearDown(self):
        """
        Remove the test work log file if it exists.
        
        Deletes the file at self.work_log_path to clean up filesystem state after a test run.
        """
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

if __name__ == '__main__':
    unittest.main()
