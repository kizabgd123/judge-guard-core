import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.kaggle_stream.kaggle_agent import KaggleAgent
import src.kaggle_stream.app as app

class TestPerformance(unittest.TestCase):
    @patch('src.antigravity_core.notion_client.NotionClient')
    def test_run_agent_turn_latency(self, mock_notion_class):
        # Setup Notion mock
        mock_notion_instance = MagicMock()
        mock_notion_class.return_value = mock_notion_instance

        def slow_notion(*args, **kwargs):
            time.sleep(0.5)
            return {"id": "page_id"}
        mock_notion_instance.append_to_database.side_effect = slow_notion

        # Setup Multimedia mock
        mock_multimedia = MagicMock()
        def slow_audio(*args, **kwargs):
            time.sleep(0.5)
            return "audio.mp3"
        def slow_image(*args, **kwargs):
            time.sleep(0.5)
            return "image.png"

        mock_multimedia.generate_audio.side_effect = slow_audio
        mock_multimedia.generate_mood_image.side_effect = slow_image

        # Inject mock multimedia and executor into app module
        with patch.object(app, 'multimedia', mock_multimedia), \
             patch.object(app, 'executor', app.executor): # ensure it's initialized if needed

            agent = KaggleAgent(name="TestAgent")
            # Patch agent._notion to ensure it uses our mock (since NotionClient is lazy)
            agent._notion = mock_notion_instance
            agent.demo_mode = True # Use demo data to avoid Gemini API calls

            print("\n--- Starting Benchmark (Baseline) ---")
            start_time = time.time()
            with patch.dict('os.environ', {'NOTION_KAGGLE_DB_ID': 'test_db'}):
                app.run_agent_turn(agent, "test task")
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration: {duration:.4f}s")
            # Expected: ~0.5s (Audio and Image are parallel, Notion is background)

if __name__ == "__main__":
    unittest.main()
