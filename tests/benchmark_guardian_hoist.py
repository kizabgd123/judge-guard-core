import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json

# Ensure src is in path
sys.path.append(os.getcwd())

from src.antigravity_core.guardian_agent import GuardianAgent

class BenchmarkGuardianHoist(unittest.TestCase):
    @patch('src.antigravity_core.guardian_agent.NotionClient')
    @patch('src.antigravity_core.guardian_agent.GeminiClient')
    def test_process_logs_scaling(self, mock_gemini_class, mock_notion_class):
        # Setup mocks
        mock_notion = mock_notion_class.return_value
        mock_gemini = mock_gemini_class.return_value

        # Scale parameters
        NUM_LOGS = 50
        NUM_GOALS = 100

        # Mock logs and goals
        logs = [{"id": f"log{i}", "properties": {"Entry": {"rich_text": [{"text": {"content": f"log entry {i}"}}]}}} for i in range(NUM_LOGS)]
        goals = [{"id": f"goal{i}", "properties": {"Name": {"id": "title", "title": [{"text": {"content": f"goal {i}"}}]}}} for i in range(NUM_GOALS)]

        mock_notion.query_database.side_effect = [logs, goals]

        # No artificial delays for pure algorithmic benchmark
        mock_gemini.generate_content.return_value = '{"match_found": false}'
        mock_notion.update_page_properties.return_value = {}

        # Environment variables for init
        with patch.dict('os.environ', {'GOALS_DB_ID': 'g', 'LOGS_DB_ID': 'l'}):
            agent = GuardianAgent()

            print(f"\n--- Starting Guardian Scaling Benchmark ({NUM_LOGS} logs, {NUM_GOALS} goals) ---")
            start_time = time.time()
            agent.process_logs()
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration: {duration:.4f}s")

if __name__ == "__main__":
    unittest.main()
