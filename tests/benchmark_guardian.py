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
    def test_process_logs_latency(self, mock_gemini_class, mock_notion_class):
        # Setup mocks
        mock_notion = mock_notion_class.return_value
        mock_gemini = mock_gemini_class.return_value

        # Mock 5 logs
        logs = [{"id": f"log{i}", "properties": {"Entry": {"title": [{"text": {"content": f"log {i}"}}]}}} for i in range(5)]
        goals = [{"id": "goal1", "properties": {"Name": {"title": [{"text": {"content": "goal 1"}}]}}}]

        # Updated: include artificial delay in database queries to demonstrate parallel fetch
        def slow_query(*args, **kwargs):
            time.sleep(1.0) # Simulate 1s query latency
            if args[0] == 'g': # goals
                return goals
            return logs

        mock_notion.query_database.side_effect = slow_query

        # Artificial delays
        def slow_gemini(*args, **kwargs):
            time.sleep(0.5) # Simulate 500ms Gemini latency
            return '{"match_found": false}'

        def slow_notion_update(*args, **kwargs):
            time.sleep(0.2) # Simulate 200ms Notion latency
            return {}

        mock_gemini.generate_content.side_effect = slow_gemini
        mock_notion.update_page_properties.side_effect = slow_notion_update

        # Environment variables for init
        with patch.dict('os.environ', {'GOALS_DB_ID': 'g', 'LOGS_DB_ID': 'l'}):
            agent = GuardianAgent()

            print("\n--- Starting Guardian Benchmark (Sequential) ---")
            start_time = time.time()
            agent.process_logs()
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration for 5 logs: {duration:.4f}s")
            # Expected: 5 * (0.5 + 0.2) = 3.5s

if __name__ == "__main__":
    unittest.main()
