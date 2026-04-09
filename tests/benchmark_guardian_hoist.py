import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.antigravity_core.guardian_agent import GuardianAgent

class BenchmarkGuardianHoist(unittest.TestCase):
    @patch('src.antigravity_core.guardian_agent.NotionClient')
    @patch('src.antigravity_core.guardian_agent.GeminiClient')
    def test_process_logs_efficiency(self, mock_gemini_class, mock_notion_class):
        # Setup mocks
        mock_notion = mock_notion_class.return_value
        mock_gemini = mock_gemini_class.return_value

        # Mock 10 logs and 50 goals to emphasize redundant string construction
        logs = [{"id": f"log{i}", "properties": {"Entry": {"title": [{"text": {"content": f"log entry {i}"}}]}}} for i in range(10)]
        goals = [{"id": f"goal{i}", "properties": {"Name": {"title": [{"text": {"content": f"goal description {i}"}}]}}} for i in range(50)]

        mock_notion.query_database.side_effect = [logs, goals]

        # Artificial delays to simulate I/O
        def fast_gemini(*args, **kwargs):
            # We use a very small delay to focus on the overhead of the loop logic itself
            # in a real scenario, this would be higher, but we want to see the "hoist" effect.
            return '{"match_found": false}'

        mock_gemini.generate_content.side_effect = fast_gemini
        mock_notion.update_page_properties.return_value = {}

        # Environment variables for init
        with patch.dict('os.environ', {'GOALS_DB_ID': 'g', 'LOGS_DB_ID': 'l'}):
            agent = GuardianAgent()

            print(f"\n--- Starting Guardian Hoist Benchmark ({len(logs)} logs, {len(goals)} goals) ---")
            start_time = time.time()
            agent.process_logs()
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration: {duration:.4f}s")

if __name__ == "__main__":
    unittest.main()
