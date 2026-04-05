import unittest
from unittest.mock import patch, MagicMock
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
        """
        Remove the test work log file if it exists.

        Deletes the file at self.work_log_path to clean up filesystem state after a test run.
        """
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)


# --- Tests for JudgeGuard BlockJudge client reuse (PR: Bolt: Offload Bridge I/O and reuse GeminiClient) ---

class TestJudgeGuardBlockJudgeClientReuse(unittest.TestCase):
    """Verify that JudgeGuard passes its own GeminiClient instance to BlockJudge
    rather than letting BlockJudge create a redundant second client."""

    def setUp(self):
        self.work_log_path = "/tmp/test_jg_client_reuse_log"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Reuse Test Action\n")

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def test_block_judge_receives_guards_gemini_client(self):
        """BlockJudge must be constructed with client=self.gemini inside verify_action."""
        import judge_guard as jg_module
        # Must patch the name as it exists in judge_guard's namespace
        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', False), \
             patch('judge_guard.PIPELINE_AVAILABLE', False), \
             patch('src.antigravity_core.gemini_client.GeminiClient') as mock_gemini_class, \
             patch('judge_guard.BlockJudge') as mock_block_judge_class:

            mock_gemini_instance = MagicMock()
            mock_gemini_class.return_value = mock_gemini_instance
            mock_block_judge_instance = MagicMock()
            mock_block_judge_instance.evaluate.return_value = True
            mock_block_judge_class.return_value = mock_block_judge_instance

            real_guard = jg_module.JudgeGuard(work_log_path=self.work_log_path)
            real_guard.gemini = mock_gemini_instance

            # Patch gemini.judge_content for Layer 3 (write operation check)
            mock_gemini_instance.judge_content.return_value = True

            with patch.object(real_guard, '_check_work_log', return_value=True), \
                 patch.object(real_guard, '_load_context', return_value="🟡 Starting"):
                real_guard.verify_action("write a new file")

            # BlockJudge must have been constructed with client= equal to the guard's own client
            _, kwargs = mock_block_judge_class.call_args
            self.assertIs(kwargs.get('client'), mock_gemini_instance)

    def test_no_extra_gemini_client_created_during_verify_action(self):
        """GeminiClient() must be called exactly once (during JudgeGuard init), not again for BlockJudge."""
        import judge_guard as jg_module
        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', False), \
             patch('judge_guard.PIPELINE_AVAILABLE', False), \
             patch('src.antigravity_core.gemini_client.GeminiClient') as mock_gemini_class, \
             patch('judge_guard.BlockJudge') as mock_block_judge_class:

            mock_gemini_instance = MagicMock()
            mock_gemini_class.return_value = mock_gemini_instance
            mock_block_judge_instance = MagicMock()
            mock_block_judge_instance.evaluate.return_value = True
            mock_block_judge_class.return_value = mock_block_judge_instance
            mock_gemini_instance.judge_content.return_value = True

            real_guard = jg_module.JudgeGuard(work_log_path=self.work_log_path)
            # Reset call count after init; from this point no new GeminiClient should be created
            mock_gemini_class.reset_mock()

            with patch.object(real_guard, '_check_work_log', return_value=True), \
                 patch.object(real_guard, '_load_context', return_value="🟡 Starting"):
                real_guard.verify_action("write a file")

            # GeminiClient() must NOT be called again inside verify_action
            mock_gemini_class.assert_not_called()


if __name__ == '__main__':
    unittest.main()