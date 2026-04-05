import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Patch dependencies globally
mock_gemini_class = MagicMock()
mock_bridge_obj = MagicMock()

# Pre-import judge_guard to ensure it uses the mocks
with patch.dict('sys.modules', {
    'src.antigravity_core.gemini_client': MagicMock(GeminiClient=mock_gemini_class),
    'src.antigravity_core.mobile_bridge': MagicMock(bridge=mock_bridge_obj)
}):
    import judge_guard
    from judge_guard import JudgeGuard

class TestJudgeGuardSecurity(unittest.TestCase):
    def setUp(self):
        """
        Set up filesystem state, mocks, and environment patches required by JudgeGuard security tests.
        
        Creates a temporary work log at /tmp/test_work_log_security.md containing an initial marker line, resets call history on the global mock objects `mock_gemini_class` and `mock_bridge_obj`, starts patches that force `judge_guard.JUDGE_AVAILABLE = True`, `judge_guard.BRIDGE_AVAILABLE = True`, and replace `judge_guard.bridge` with `mock_bridge_obj` (stored in `self.jg_patchers`), and instantiates a `JudgeGuard` assigned to `self.judge`.
        """
        self.work_log_path = "/tmp/test_work_log_security.md"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting test action\n")

        mock_gemini_class.reset_mock()
        mock_bridge_obj.reset_mock()

        # Ensure JudgeGuard uses our mocks for every test
        self.jg_patchers = [
            patch('judge_guard.JUDGE_AVAILABLE', True),
            patch('judge_guard.BRIDGE_AVAILABLE', True),
            patch('judge_guard.bridge', mock_bridge_obj)
        ]
        for p in self.jg_patchers:
            p.start()

        # Instantiate JudgeGuard
        # We need to mock judge_content on the instance's gemini object for some tests
        self.judge = JudgeGuard(work_log_path=self.work_log_path)

    def tearDown(self):
        """
        Remove the temporary work log file and stop patchers.
        """
        for p in self.jg_patchers:
            p.stop()

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
        mock_bridge_obj.push_verdict.assert_called()

    def test_safe_command(self):
        # For safe commands, we need to mock deeper layers
        """
        Verifies that a benign shell command is permitted when deeper validation layers approve.
        
        Patches the block-level evaluator and Gemini content judge to return True, calls verify_action with "ls -la", and asserts the action is allowed.
        """
        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True),              patch.object(self.judge.gemini, 'judge_content', return_value=True):

            action = "ls -la"
            result = self.judge.verify_action(action)
            self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
