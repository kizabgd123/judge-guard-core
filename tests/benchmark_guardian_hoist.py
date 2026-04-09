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
    def test_hoist_scaling(self, mock_gemini_class, mock_notion_class):
    def test_process_logs_efficiency(self, mock_gemini_class, mock_notion_class):
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
        NUM_GOALS = 20

        # Mock logs and goals with large data
        logs = [{"id": f"log{i}", "properties": {"Entry": {"title": [{"text": {"content": f"Log entry number {i} with some extra text for processing overhead."}}]}}} for i in range(NUM_LOGS)]
        goals = [{"id": f"goal{j}", "properties": {"Name": {"title": [{"text": {"content": f"Target goal {j} with a reasonably long description to simulate real-world data."}}]}}} for j in range(NUM_GOALS)]

        mock_notion.query_database.side_effect = [logs, goals]

        # Artificial delays (but making them fast to focus on string overhead)
        mock_gemini.generate_content.return_value = '{"match_found": false}'
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

            print(f"\n--- Starting Guardian Scaling Benchmark ({NUM_LOGS} logs, {NUM_GOALS} goals) ---")
            print(f"\n--- Starting Guardian Benchmark (Scaling: {NUM_LOGS} logs, {NUM_GOALS} goals) ---")

            # Warm up
            agent._get_title(logs[0])

            print(f"\n--- Starting Guardian Hoist Benchmark ({len(logs)} logs, {len(goals)} goals) ---")
            start_time = time.time()
            agent.process_logs()
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration: {duration:.4f}s")

if __name__ == "__main__":
    unittest.main()
