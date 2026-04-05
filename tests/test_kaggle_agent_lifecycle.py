import sys
import unittest
from unittest.mock import MagicMock
# Mock google.generativeai before project imports try to load it
sys.modules.setdefault('google', MagicMock())
sys.modules.setdefault('google.generativeai', MagicMock())

from unittest.mock import patch, call
from src.kaggle_stream.kaggle_agent import KaggleAgent
import os

class TestKaggleAgentLifecycle(unittest.TestCase):
    def test_executor_shutdown_on_close(self):
        agent = KaggleAgent(name="LifecycleTest")
        executor = agent._executor
        self.assertFalse(executor._shutdown)
        agent.close()
        self.assertTrue(executor._shutdown)

    def test_context_manager_shutdown(self):
        with KaggleAgent(name="ContextTest") as agent:
            executor = agent._executor
            self.assertFalse(executor._shutdown)
        self.assertTrue(executor._shutdown)


# --- Tests for KaggleAgent notion_db_id caching (PR: Bolt: Offload Bridge I/O and reuse GeminiClient) ---

class TestKaggleAgentNotionDbIdCache(unittest.TestCase):
    def test_notion_db_id_cached_at_init_from_env(self):
        """notion_db_id must be set from the environment variable during __init__."""
        with patch.dict(os.environ, {"NOTION_KAGGLE_DB_ID": "test-db-123"}):
            agent = KaggleAgent(name="CacheTest")
            self.assertEqual(agent.notion_db_id, "test-db-123")
            agent.close()

    def test_notion_db_id_is_none_when_env_unset(self):
        """notion_db_id must be None when NOTION_KAGGLE_DB_ID is not in the environment."""
        env = {k: v for k, v in os.environ.items() if k != "NOTION_KAGGLE_DB_ID"}
        with patch.dict(os.environ, env, clear=True):
            agent = KaggleAgent(name="NoCacheTest")
            self.assertIsNone(agent.notion_db_id)
            agent.close()

    def test_log_to_notion_uses_cached_db_id_not_getenv(self):
        """_log_to_notion must check self.notion_db_id, not call os.getenv each time."""
        with patch.dict(os.environ, {"NOTION_KAGGLE_DB_ID": "cached-db-id"}):
            agent = KaggleAgent(name="CachedCallTest")
            mock_notion = MagicMock()
            agent.notion = mock_notion

            with patch('os.getenv') as mock_getenv:
                agent._log_to_notion({"status": "ok", "accuracy": 0.9, "total_progress": 50})
                # os.getenv should NOT be consulted for NOTION_KAGGLE_DB_ID inside _log_to_notion
                for c in mock_getenv.call_args_list:
                    self.assertNotEqual(c, call("NOTION_KAGGLE_DB_ID"))

            agent.close()

    def test_execute_notion_append_uses_cached_db_id(self):
        """_execute_notion_append must call append_to_database with self.notion_db_id."""
        with patch.dict(os.environ, {"NOTION_KAGGLE_DB_ID": "my-db-999"}):
            agent = KaggleAgent(name="AppendTest")
            mock_notion = MagicMock()
            agent.notion = mock_notion

            data = {
                "status": "success",
                "message": "test msg",
                "mood": "happy",
                "accuracy": 0.85,
                "total_progress": 40,
            }
            agent._execute_notion_append(data)

            mock_notion.append_to_database.assert_called_once()
            called_db_id = mock_notion.append_to_database.call_args[0][0]
            self.assertEqual(called_db_id, "my-db-999")
            agent.close()

    def test_log_to_notion_skips_when_db_id_is_demo(self):
        """_log_to_notion must not submit a task when notion_db_id is 'demo'."""
        with patch.dict(os.environ, {"NOTION_KAGGLE_DB_ID": "demo"}):
            agent = KaggleAgent(name="DemoTest")
            mock_notion = MagicMock()
            agent.notion = mock_notion

            # Wrap the real executor's submit to observe calls without replacing it
            real_submit = agent._executor.submit
            submit_calls = []

            def tracking_submit(fn, *args, **kwargs):
                submit_calls.append(fn)
                return real_submit(fn, *args, **kwargs)

            agent._executor.submit = tracking_submit
            agent._log_to_notion({"status": "ok"})
            agent.close()

            self.assertEqual(submit_calls, [])

    def test_log_to_notion_skips_when_db_id_is_none(self):
        """_log_to_notion must not submit a task when notion_db_id is None."""
        env = {k: v for k, v in os.environ.items() if k != "NOTION_KAGGLE_DB_ID"}
        with patch.dict(os.environ, env, clear=True):
            agent = KaggleAgent(name="NullDbTest")
            mock_notion = MagicMock()
            agent.notion = mock_notion

            real_submit = agent._executor.submit
            submit_calls = []

            def tracking_submit(fn, *args, **kwargs):
                submit_calls.append(fn)
                return real_submit(fn, *args, **kwargs)

            agent._executor.submit = tracking_submit
            agent._log_to_notion({"status": "ok"})
            agent.close()

            self.assertEqual(submit_calls, [])


if __name__ == "__main__":
    unittest.main()