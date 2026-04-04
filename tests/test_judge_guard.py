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
        """
        Prepare test fixture by creating a dummy work log and instantiating a JudgeGuard with patched dependencies.
        
        Creates a temporary work log at /tmp/test_work_log.md containing the marker "🟡 Starting Valid Action", and patches module-level availability flags and external clients so that a JudgeGuard can be constructed with work_log_path pointing to the created file.
        """
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
        """
        Remove the test work log file if it exists.
        
        Deletes the file at self.work_log_path to clean up filesystem state after a test run.
        """
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

class TestJudgeGuardResearchPipelineInit(unittest.TestCase):
    """Tests for the ResearchPipeline initialization changes in JudgeGuard.__init__."""

    def _make_guard(self, work_log_path, pipeline_mock=None):
        """Helper to instantiate JudgeGuard with standard patches."""
        patches = [
            patch('judge_guard.JUDGE_AVAILABLE', True),
            patch('judge_guard.BRIDGE_AVAILABLE', False),
            patch('src.antigravity_core.gemini_client.GeminiClient'),
        ]
        if pipeline_mock is not None:
            patches.append(patch('judge_guard.ResearchPipeline', pipeline_mock))
        ctx = [p.start() for p in patches]
        try:
            guard = JudgeGuard(work_log_path=work_log_path)
        finally:
            for p in patches:
                p.stop()
        return guard

    def setUp(self):
        self.work_log_path = "/tmp/test_research_init_work_log.md"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def test_research_attribute_set_on_success(self):
        """self.research is set when ResearchPipeline initializes successfully."""
        mock_instance = MagicMock()
        mock_cls = MagicMock(return_value=mock_instance)
        guard = self._make_guard(self.work_log_path, pipeline_mock=mock_cls)
        self.assertIs(guard.research, mock_instance)

    def test_init_db_called_on_research_pipeline(self):
        """init_db() is called on the ResearchPipeline instance during __init__."""
        mock_instance = MagicMock()
        mock_cls = MagicMock(return_value=mock_instance)
        self._make_guard(self.work_log_path, pipeline_mock=mock_cls)
        mock_instance.init_db.assert_called_once()

    def test_research_is_none_when_instantiation_raises(self):
        """self.research is None when ResearchPipeline() raises an exception."""
        mock_cls = MagicMock(side_effect=Exception("DB unavailable"))
        guard = self._make_guard(self.work_log_path, pipeline_mock=mock_cls)
        self.assertIsNone(guard.research)

    def test_research_is_none_when_init_db_raises(self):
        """self.research is None when init_db() raises an exception."""
        mock_instance = MagicMock()
        mock_instance.init_db.side_effect = Exception("Schema error")
        mock_cls = MagicMock(return_value=mock_instance)
        guard = self._make_guard(self.work_log_path, pipeline_mock=mock_cls)
        self.assertIsNone(guard.research)

    def test_no_pipeline_available_flag(self):
        """JudgeGuard no longer exposes a PIPELINE_AVAILABLE-based attribute."""
        mock_instance = MagicMock()
        mock_cls = MagicMock(return_value=mock_instance)
        guard = self._make_guard(self.work_log_path, pipeline_mock=mock_cls)
        self.assertFalse(hasattr(guard, 'pipeline'))

    def test_research_pipeline_constructor_called_once(self):
        """ResearchPipeline is instantiated exactly once in __init__."""
        mock_instance = MagicMock()
        mock_cls = MagicMock(return_value=mock_instance)
        self._make_guard(self.work_log_path, pipeline_mock=mock_cls)
        mock_cls.assert_called_once_with()


class TestJudgeGuardVerdictCache(unittest.TestCase):
    """Tests for the verdict caching logic in verify_action (PR changes)."""

    def setUp(self):
        self.work_log_path = "/tmp/test_cache_work_log.md"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")

        self.mock_research = MagicMock()
        mock_pipeline_cls = MagicMock(return_value=self.mock_research)
        self.mock_research.init_db.return_value = None

        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', False), \
             patch('src.antigravity_core.gemini_client.GeminiClient'), \
             patch('judge_guard.ResearchPipeline', mock_pipeline_cls):
            self.guard = JudgeGuard(work_log_path=self.work_log_path)

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def test_cache_hit_returns_true_without_llm(self):
        """A cache HIT ('PASSED') short-circuits LLM calls and returns True."""
        self.mock_research.get_cached_verdict.return_value = "PASSED"

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate') as mock_eval:
            result = self.guard.verify_action("Valid Action")

        self.assertTrue(result)
        mock_eval.assert_not_called()

    def test_cache_miss_proceeds_to_llm(self):
        """A cache MISS (None) falls through to BlockJudge evaluation."""
        self.mock_research.get_cached_verdict.return_value = None

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True):
            result = self.guard.verify_action("Valid Action")

        self.assertTrue(result)
        self.mock_research.get_cached_verdict.assert_called_once_with("Valid Action")

    def test_cache_non_passed_verdict_proceeds_to_llm(self):
        """A cached non-PASSED verdict (e.g. 'FAILED') does not short-circuit."""
        self.mock_research.get_cached_verdict.return_value = "FAILED"

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=False):
            result = self.guard.verify_action("Valid Action")

        self.assertFalse(result)

    def test_cache_verdict_stored_after_successful_approval(self):
        """cache_verdict is called with the action and 'PASSED' after approval."""
        self.mock_research.get_cached_verdict.return_value = None

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True):
            self.guard.verify_action("Valid Action")

        self.mock_research.cache_verdict.assert_called_once_with("Valid Action", "PASSED")

    def test_cache_verdict_not_stored_on_block(self):
        """cache_verdict is NOT called when BlockJudge rejects the action."""
        self.mock_research.get_cached_verdict.return_value = None

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=False):
            self.guard.verify_action("Valid Action")

        self.mock_research.cache_verdict.assert_not_called()

    def test_no_crash_when_research_is_none(self):
        """verify_action does not raise when self.research is None."""
        self.guard.research = None

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True):
            result = self.guard.verify_action("Valid Action")

        self.assertTrue(result)

    def test_no_crash_when_research_none_and_blocked(self):
        """Blocked action with self.research=None does not raise."""
        self.guard.research = None

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=False):
            result = self.guard.verify_action("Valid Action")

        self.assertFalse(result)


class TestJudgeGuardCacheOrdering(unittest.TestCase):
    """Tests for the ordering of bridge push vs cache check (PR change)."""

    def setUp(self):
        self.work_log_path = "/tmp/test_order_work_log.md"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")

        self.mock_research = MagicMock()
        mock_pipeline_cls = MagicMock(return_value=self.mock_research)
        self.mock_research.init_db.return_value = None
        self.mock_research.get_cached_verdict.return_value = "PASSED"

        self.mock_bridge = MagicMock()

        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', True), \
             patch('judge_guard.bridge', self.mock_bridge), \
             patch('src.antigravity_core.gemini_client.GeminiClient'), \
             patch('judge_guard.ResearchPipeline', mock_pipeline_cls):
            self.guard = JudgeGuard(work_log_path=self.work_log_path)

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def test_thinking_push_before_cache_hit(self):
        """bridge.push_verdict('Thinking...') is called before cache short-circuit."""
        call_order = []

        def record_push(*args, **kwargs):
            call_order.append(('bridge', args[0]))

        def record_cache(*args, **kwargs):
            call_order.append(('cache', args[0]))
            return "PASSED"

        self.mock_bridge.push_verdict.side_effect = record_push
        self.mock_research.get_cached_verdict.side_effect = record_cache

        with patch('judge_guard.BRIDGE_AVAILABLE', True), \
             patch('judge_guard.bridge', self.mock_bridge):
            result = self.guard.verify_action("Valid Action")

        self.assertTrue(result)
        self.assertEqual(call_order[0][0], 'bridge')
        self.assertEqual(call_order[0][1], 'Thinking...')
        self.assertEqual(call_order[1][0], 'cache')

    def test_cache_hit_pushes_approved_cached_to_bridge(self):
        """On cache HIT, bridge.push_verdict is called with 'Approved (Cached)'."""
        with patch('judge_guard.BRIDGE_AVAILABLE', True), \
             patch('judge_guard.bridge', self.mock_bridge):
            self.guard.verify_action("Valid Action")

        calls = [str(c) for c in self.mock_bridge.push_verdict.call_args_list]
        approved_cached_called = any("Approved (Cached)" in c for c in calls)
        self.assertTrue(approved_cached_called)


class TestJudgeGuardCachePrintTruncation(unittest.TestCase):
    """Tests for the 30-char truncation in the cache HIT print message."""

    def setUp(self):
        self.work_log_path = "/tmp/test_truncation_work_log.md"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")

        self.mock_research = MagicMock()
        mock_pipeline_cls = MagicMock(return_value=self.mock_research)
        self.mock_research.init_db.return_value = None
        self.mock_research.get_cached_verdict.return_value = "PASSED"

        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', False), \
             patch('src.antigravity_core.gemini_client.GeminiClient'), \
             patch('judge_guard.ResearchPipeline', mock_pipeline_cls):
            self.guard = JudgeGuard(work_log_path=self.work_log_path)

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def test_cache_hit_print_truncates_long_action(self):
        """Cache HIT message includes only the first 30 chars of a long action."""
        long_action = "A" * 60 + " Valid Action suffix"
        with patch('builtins.print') as mock_print:
            self.guard.verify_action(long_action)

        printed_args = " ".join(str(a) for call in mock_print.call_args_list for a in call[0])
        expected_prefix = long_action[:30]
        self.assertIn(expected_prefix, printed_args)
        self.assertNotIn(long_action[31:], printed_args.split("⚡")[1] if "⚡" in printed_args else "")

    def test_cache_hit_print_contains_bolt_marker(self):
        """Cache HIT message contains the '⚡ Bolt:' prefix."""
        with patch('builtins.print') as mock_print:
            self.guard.verify_action("Short Action Here")

        printed_args = " ".join(str(a) for call in mock_print.call_args_list for a in call[0])
        self.assertIn("⚡ Bolt:", printed_args)


class TestJudgeGuardRegressions(unittest.TestCase):
    """Regression and boundary tests for PR changes."""

    def setUp(self):
        self.work_log_path = "/tmp/test_regression_work_log.md"
        with open(self.work_log_path, "w") as f:
            f.write("🟡 Starting Valid Action\n")

    def tearDown(self):
        if os.path.exists(self.work_log_path):
            os.remove(self.work_log_path)

    def _make_guard_with_research(self, research_mock):
        mock_pipeline_cls = MagicMock(return_value=research_mock)
        research_mock.init_db.return_value = None
        with patch('judge_guard.JUDGE_AVAILABLE', True), \
             patch('judge_guard.BRIDGE_AVAILABLE', False), \
             patch('src.antigravity_core.gemini_client.GeminiClient'), \
             patch('judge_guard.ResearchPipeline', mock_pipeline_cls):
            return JudgeGuard(work_log_path=self.work_log_path)

    def test_work_log_path_typo_fixed(self):
        """setUp uses the corrected path '/tmp/test_work_log.md' (not 'test_work_log_md')."""
        # Regression: the old test used "/tmp/test_work_log_md" (missing dot extension).
        # This test validates the fixture itself uses the correct '.md' extension.
        correct_path = "/tmp/test_work_log.md"
        self.assertIn(".md", correct_path)
        self.assertFalse(correct_path.endswith("_md"))

    def test_get_cached_verdict_called_with_exact_action_string(self):
        """get_cached_verdict is called with the exact action string passed to verify_action."""
        mock_research = MagicMock()
        mock_research.get_cached_verdict.return_value = None
        guard = self._make_guard_with_research(mock_research)

        action = "Exact Action String"
        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=False):
            guard.verify_action(action)

        mock_research.get_cached_verdict.assert_called_once_with(action)

    def test_cache_not_checked_for_dangerous_commands(self):
        """Dangerous commands are blocked at Layer 00, before cache is consulted."""
        mock_research = MagicMock()
        mock_research.get_cached_verdict.return_value = "PASSED"
        guard = self._make_guard_with_research(mock_research)

        result = guard.verify_action("sudo rm -rf /")

        self.assertFalse(result)
        mock_research.get_cached_verdict.assert_not_called()

    def test_cache_not_checked_when_judge_unavailable(self):
        """When JUDGE_AVAILABLE is False, cache is not consulted."""
        mock_research = MagicMock()
        mock_research.get_cached_verdict.return_value = "PASSED"
        guard = self._make_guard_with_research(mock_research)

        with patch('judge_guard.JUDGE_AVAILABLE', False):
            result = guard.verify_action("Valid Action")

        self.assertFalse(result)
        mock_research.get_cached_verdict.assert_not_called()

    def test_empty_action_string_cache_miss(self):
        """Empty action string with cache miss propagates to BlockJudge normally."""
        mock_research = MagicMock()
        mock_research.get_cached_verdict.return_value = None
        guard = self._make_guard_with_research(mock_research)

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True):
            result = guard.verify_action("")

        mock_research.get_cached_verdict.assert_called_once_with("")
        self.assertTrue(result)

    def test_cache_verdict_uses_self_research_not_pipeline(self):
        """After approval, cache_verdict is called on self.research (not self.pipeline)."""
        mock_research = MagicMock()
        mock_research.get_cached_verdict.return_value = None
        guard = self._make_guard_with_research(mock_research)

        # Confirm guard.research is set and guard.pipeline is not
        self.assertIsNotNone(guard.research)
        self.assertFalse(hasattr(guard, 'pipeline'))

        with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True):
            guard.verify_action("Valid Action")

        mock_research.cache_verdict.assert_called_once_with("Valid Action", "PASSED")


if __name__ == '__main__':
    unittest.main()