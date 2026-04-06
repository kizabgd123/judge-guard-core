import time
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mocking modules before import
sys.modules['src.antigravity_core.notion_client'] = MagicMock()
sys.modules['src.antigravity_core.gemini_client'] = MagicMock()

from src.antigravity_core.guardian_agent import GuardianAgent

def run_benchmark():
    # Setup environment
    os.environ["GOALS_DB_ID"] = "test_goals"
    os.environ["LOGS_DB_ID"] = "test_logs"

    # Create mock NotionClient instance
    mock_notion = MagicMock()
    # Mock return values for fetch_unprocessed_logs and fetch_active_goals
    # 5 logs
    mock_notion.query_database.side_effect = [
        [{"id": f"log{i}", "properties": {"Entry": {"title": [{"text": {"content": f"log text {i}"}}]}}} for i in range(5)], # logs
        [{"id": "goal1", "properties": {"Name": {"title": [{"text": {"content": "goal text"}}]}}}]  # goals
    ]

    def slow_notion_update(*args, **kwargs):
        time.sleep(0.2) # 200ms latency
        return {}

    mock_notion.update_page_properties.side_effect = slow_notion_update

    # Create mock GeminiClient instance
    mock_gemini = MagicMock()
    def slow_gemini_generate(*args, **kwargs):
        time.sleep(0.5) # 500ms latency
        return '{"match_found": true, "goal_id": "goal1", "progress_comment": "Worked on it"}'

    mock_gemini.generate_content.side_effect = slow_gemini_generate

    with patch('src.antigravity_core.guardian_agent.NotionClient', return_value=mock_notion), \
         patch('src.antigravity_core.guardian_agent.GeminiClient', return_value=mock_gemini):

        agent = GuardianAgent()

        print("--- Starting GuardianAgent Benchmark ---")
        start_time = time.time()
        agent.process_logs()
        end_time = time.time()

        duration = end_time - start_time
        print(f"Total processing time for 5 logs: {duration:.4f}s")
        print(f"Average time per log: {duration/5:.4f}s")

if __name__ == "__main__":
    run_benchmark()
