import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.antigravity_core.guardian_agent import GuardianAgent

class BenchmarkGuardianBolt(unittest.TestCase):
    @patch('src.antigravity_core.guardian_agent.NotionClient')
    @patch('src.antigravity_core.guardian_agent.GeminiClient')
    def test_no_goals_performance(self, mock_gemini_class, mock_notion_class):
        # Setup mocks
        mock_notion = mock_notion_class.return_value
        mock_gemini = mock_gemini_class.return_value

        # Mock 10 logs, but 0 goals
        logs = [{"id": f"log{i}", "properties": {"Entry": {"id": "title", "title": [{"text": {"content": f"log {i}"}}]}}} for i in range(10)]
        goals = []

        mock_notion.query_database.side_effect = lambda db, filter: goals if db == 'g' else logs

        # We don't want Gemini to actually be called
        mock_gemini.generate_content.return_value = '{"match_found": false}'

        # Environment variables for init
        with patch.dict('os.environ', {'GOALS_DB_ID': 'g', 'LOGS_DB_ID': 'l'}):
            agent = GuardianAgent()

            print("\n--- Starting Guardian 'No Goals' Benchmark ---")
            start_time = time.time()
            agent.process_logs()
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration for 10 logs with 0 goals: {duration:.4f}s")

            call_count = mock_gemini.generate_content.call_count
            print(f"Gemini call count: {call_count}")

            # Assert that Gemini was NOT called when no goals exist
            self.assertEqual(call_count, 0, "Gemini should not be called when no goals exist.")

    @patch('src.antigravity_core.guardian_agent.NotionClient')
    @patch('src.antigravity_core.guardian_agent.GeminiClient')
    def test_no_logs_performance(self, mock_gemini_class, mock_notion_class):
        # Setup mocks
        mock_notion = mock_notion_class.return_value

        # Mock 0 logs, 10 goals
        logs = []
        goals = [{"id": f"goal{i}", "properties": {"Name": {"id": "title", "title": [{"text": {"content": f"goal {i}"}}]}}} for i in range(10)]

        mock_notion.query_database.side_effect = lambda db, filter: goals if db == 'g' else logs

        # Environment variables for init
        with patch.dict('os.environ', {'GOALS_DB_ID': 'g', 'LOGS_DB_ID': 'l'}):
            agent = GuardianAgent()

            print("\n--- Starting Guardian 'No Logs' Benchmark ---")
            start_time = time.time()
            agent.process_logs()
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration for 0 logs with 10 goals: {duration:.4f}s")

            # Verify that query_database for goals was NOT called because logs were empty
            # query_database for logs is called once.
            self.assertEqual(mock_notion.query_database.call_count, 1, "Only logs should be queried when no logs are found.")
            mock_notion.query_database.assert_called_with('l', {"property": "Processed", "checkbox": {"equals": False}})

if __name__ == "__main__":
    unittest.main()
