import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.antigravity_core.guardian_agent import GuardianAgent

class BenchmarkGuardian(unittest.TestCase):
    @patch('src.antigravity_core.guardian_agent.NotionClient')
    @patch('src.antigravity_core.guardian_agent.GeminiClient')
    def test_process_logs_benchmark(self, mock_gemini_class, mock_notion_class):
        # Setup environment variables
        os.environ["GOALS_DB_ID"] = "test_goals_db"
        os.environ["LOGS_DB_ID"] = "test_logs_db"

        # Setup Notion mock
        mock_notion = mock_notion_class.return_value

        # Artificial delays
        GEMINI_DELAY = 0.5
        NOTION_DELAY = 0.2
        NUM_LOGS = 5

        def slow_notion_update(*args, **kwargs):
            time.sleep(NOTION_DELAY) # Simulate Notion API latency
            return {}

        mock_notion.query_database.side_effect = [
            [{"id": "goal1", "properties": {"Name": {"title": [{"text": {"content": "goal text"}}]}}}], # goals
            [{"id": f"log{i}", "properties": {"Entry": {"title": [{"text": {"content": f"log content {i}"}}]}}} for i in range(NUM_LOGS)] # logs
        ]
        # Important: Notion update is called per log.
        mock_notion.update_page_properties.side_effect = slow_notion_update

        # Setup Gemini mock
        mock_gemini = mock_gemini_class.return_value

        def slow_gemini_generate(*args, **kwargs):
            time.sleep(GEMINI_DELAY) # Simulate Gemini API latency
            return '{"match_found": true, "goal_id": "goal1", "progress_comment": "Progress made"}'

        mock_gemini.generate_content.side_effect = slow_gemini_generate

        agent = GuardianAgent()

        print(f"\n--- Starting Guardian Benchmark ({NUM_LOGS} Logs) ---")
        print(f"Artificial Delays: Gemini={GEMINI_DELAY}s, Notion={NOTION_DELAY}s")

        start_time = time.time()
        agent.process_logs()

        # If the agent has a close method, call it to wait for threads
        if hasattr(agent, "close"):
            agent.close()

        end_time = time.time()
        duration = end_time - start_time

        expected_sequential = (GEMINI_DELAY + NOTION_DELAY) * NUM_LOGS
        # With max_workers=5 and NUM_LOGS=5, it should be close to GEMINI_DELAY + NOTION_DELAY
        expected_parallel = GEMINI_DELAY + NOTION_DELAY

        print(f"Total duration: {duration:.4f}s")
        print(f"Expected Sequential: ~{expected_sequential:.1f}s")
        print(f"Expected Parallel (if max_workers >= logs): ~{expected_parallel:.1f}s")

        speedup = expected_sequential / duration if duration > 0 else 0
        print(f"Calculated Speedup: {speedup:.2f}x")

if __name__ == "__main__":
    unittest.main()
