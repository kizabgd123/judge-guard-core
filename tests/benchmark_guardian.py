import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

# Force environment variables for initialization
os.environ["GOALS_DB_ID"] = "test_goals"
os.environ["LOGS_DB_ID"] = "test_logs"

from src.antigravity_core.guardian_agent import GuardianAgent

class BenchmarkGuardian(unittest.TestCase):
    @patch('src.antigravity_core.guardian_agent.NotionClient')
    @patch('src.antigravity_core.guardian_agent.GeminiClient')
    def test_process_logs_latency(self, mock_gemini_class, mock_notion_class):
        # Setup Notion mock
        mock_notion = mock_notion_class.return_value

        # GuardianAgent.process_logs calls fetch_unprocessed_logs then fetch_active_goals
        # fetch_unprocessed_logs -> query_database
        # fetch_active_goals -> query_database

        mock_notion.query_database.side_effect = [
            [{"id": f"log{i}", "properties": {"Entry": {"title": [{"text": {"content": f"log {i}"}}]}}} for i in range(5)], # fetch_unprocessed_logs
            [] # fetch_active_goals
        ]

        def slow_notion_update(*args, **kwargs):
            time.sleep(0.2) # Simulate Notion API latency
            return {}
        mock_notion.update_page_properties.side_effect = slow_notion_update

        # Setup Gemini mock
        mock_gemini = mock_gemini_class.return_value
        def slow_gemini(*args, **kwargs):
            time.sleep(0.5) # Simulate Gemini API latency
            return '{"match_found": false}'
        mock_gemini.generate_content.side_effect = slow_gemini

        agent = GuardianAgent()

        print("\n--- Starting Guardian Benchmark ---")
        start_time = time.time()
        agent.process_logs()
        end_time = time.time()

        duration = end_time - start_time
        print(f"Total duration for 5 logs: {duration:.4f}s")
        # Expected baseline: 5 * (0.5s + 0.2s) = 3.5s

if __name__ == "__main__":
    unittest.main()
