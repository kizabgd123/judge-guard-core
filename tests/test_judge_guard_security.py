import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Patch dependencies globally
mock_gemini_class = MagicMock()
mock_bridge_obj = MagicMock()

with patch.dict('sys.modules', {
    'src.antigravity_core.gemini_client': MagicMock(GeminiClient=mock_gemini_class),
    'src.antigravity_core.mobile_bridge': MagicMock(bridge=mock_bridge_obj)
}):
    from judge_guard import JudgeGuard

class TestJudgeGuardSecurity(unittest.TestCase):
    def setUp(self):
        """
        Prepare the test environment for JudgeGuard security tests.
        
        Creates a temporary work log file at /tmp/test_work_log_security.md and writes an initial log entry, resets the shared Gemini and bridge mocks, and patches judge_guard.JUDGE_AVAILABLE and judge_guard.BRIDGE_AVAILABLE to True while instantiating a JudgeGuard configured to use the temporary work log.
        """
        self.work_log_path = "/tmp/test_work_log_security.md"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting test action\n")

        mock_gemini_class.reset_mock()
        mock_bridge_obj.reset_mock()

        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', True):
            self.judge = JudgeGuard(work_log_path=self.work_log_path)

    def tearDown(self):
        """
        Remove the temporary work log file created for the test.
        
        If a file exists at self.work_log_path, it is deleted to ensure test-side effects are cleaned up.
        """
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def test_dangerous_command_sudo(self):
        action = "sudo rm -rf /"
        result = self.judge.verify_action(action)
        self.assertFalse(result)
        # Check that bridge.push_verdict was called
        mock_bridge_obj.push_verdict.assert_called_with(action, "BLOCKED", "Security Violation: Action contains forbidden dangerous commands (sudo/root deletion).")

    def test_dangerous_command_root_delete(self):
        action = "rm -rf /*"
        result = self.judge.verify_action(action)
        self.assertFalse(result)

    def test_safe_command(self):
        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True), \
             patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', True):
            # Mock Layer 3
            self.judge.gemini.judge_content.return_value = True

            action = "ls -la"
            result = self.judge.verify_action(action)
            self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
