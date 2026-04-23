import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.antigravity_core.guardian_agent import GuardianAgent

class BenchmarkGuardianBoltV4(unittest.TestCase):
    @patch('src.antigravity_core.notion_client.NotionClient')
    @patch('src.antigravity_core.gemini_client.GeminiClient')
    def test_performance_scenarios(self, mock_gemini_class, mock_notion_class):
        # Setup mocks
        mock_notion = mock_notion_class.return_value
        mock_gemini = mock_gemini_class.return_value

        # Mock latencies
        def slow_query(db_id, filter_criteria):
            time.sleep(0.5) # 500ms for any Notion query
            if db_id == 'goals_id':
                return self.current_goals
            return self.current_logs

        mock_notion.query_database.side_effect = slow_query

        def slow_update(*args, **kwargs):
            time.sleep(0.1) # 100ms for Notion update
            return {}
        mock_notion.update_page_properties.side_effect = slow_update

        def slow_gemini(*args, **kwargs):
            time.sleep(1.0) # 1s for Gemini
            return '{"match_found": false}'
        mock_gemini.generate_content.side_effect = slow_gemini

        with patch.dict('os.environ', {'GOALS_DB_ID': 'goals_id', 'LOGS_DB_ID': 'logs_id'}):
            agent = GuardianAgent()

            # Scenario A: Idle (0 logs, 1 goal)
            self.current_logs = []
            self.current_goals = [{"id": "goal1", "properties": {"title": {"id": "title", "title": [{"text": {"content": "Goal 1"}}]}}}]

            print("\n--- Scenario A: Idle (0 logs) ---")
            # Idle should only call fetch_unprocessed_logs (500ms) and skip fetch_active_goals
            start = time.time()
            agent.process_logs()
            idle_duration = time.time() - start
            print(f"Duration: {idle_duration:.4f}s")
            self.assertLess(idle_duration, 0.6) # Should be ~0.5s

            # Scenario B: No Goals (5 logs, 0 goals)
            self.current_logs = [{"id": f"log{i}", "properties": {"title": {"id": "title", "title": [{"text": {"content": f"Log {i}"}}]}}} for i in range(5)]
            self.current_goals = []

            print("\n--- Scenario B: No Goals (5 logs, 0 goals) ---")
            # Should call fetch_unprocessed_logs (0.5), fetch_active_goals (0.5), then 5x update (0.1 each, parallelized)
            # Total expected: 0.5 + 0.5 + 0.1 = 1.1s
            start = time.time()
            agent.process_logs()
            no_goals_duration = time.time() - start
            print(f"Duration: {no_goals_duration:.4f}s")
            self.assertLess(no_goals_duration, 1.2)

            # Scenario C: Active (1 log, 1 goal)
            self.current_logs = [{"id": "log1", "properties": {"title": {"id": "title", "title": [{"text": {"content": "Log 1"}}]}}}]
            self.current_goals = [{"id": "goal1", "properties": {"title": {"id": "title", "title": [{"text": {"content": "Goal 1"}}]}}}]

            print("\n--- Scenario C: Active (1 log, 1 goal) ---")
            # Should call fetch_unprocessed_logs (0.5), fetch_active_goals (0.5), then 1x Gemini (1.0), then 1x update (0.1)
            # Total expected: 0.5 + 0.5 + 1.0 + 0.1 = 2.1s
            start = time.time()
            agent.process_logs()
            active_duration = time.time() - start
            print(f"Duration: {active_duration:.4f}s")
            self.assertLess(active_duration, 2.3)

if __name__ == "__main__":
    unittest.main()
