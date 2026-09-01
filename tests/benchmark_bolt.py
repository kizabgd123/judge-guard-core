import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

# Mock gradio to avoid heavy import and GUI execution during testing
sys.modules['gradio'] = MagicMock()

from src.kaggle_stream.kaggle_agent import KaggleAgent
from src.kaggle_stream.app import run_agent_turn

class TestPerformance(unittest.TestCase):
    @patch('src.antigravity_core.notion_client.NotionClient')
    @patch('src.kaggle_stream.multimedia.MultimediaManager')
    def test_run_agent_turn_latency(self, mock_multimedia_class, mock_notion_class):
        # Setup Notion mock
        mock_notion_instance = MagicMock()
        mock_notion_class.return_value = mock_notion_instance

        def slow_notion(*args, **kwargs):
            time.sleep(0.5)
            return {"id": "page_id"}
        mock_notion_instance.append_to_database.side_effect = slow_notion

        # Setup Multimedia mock
        mock_multimedia_instance = mock_multimedia_class.return_value

        def slow_audio(*args, **kwargs):
            time.sleep(0.5)
            return "audio.mp3"
        def slow_image(*args, **kwargs):
            time.sleep(0.5)
            return "image.png"

        mock_multimedia_instance.generate_audio.side_effect = slow_audio
        mock_multimedia_instance.generate_mood_image.side_effect = slow_image

        agent = KaggleAgent(name="TestAgent")
        # In KaggleAgent.__init__, it might fail to init Notion if no key.
        # We manually set it for the test.
        agent._notion = mock_notion_instance
        agent.demo_mode = True # Use demo data to avoid Gemini API calls

        print("\n--- Starting Benchmark (Baseline) ---")
        start_time = time.time()
        with patch.dict('os.environ', {'NOTION_KAGGLE_DB_ID': 'test_db'}):
            run_agent_turn(agent, "test task")
        end_time = time.time()

        duration = end_time - start_time
        print(f"Total duration: {duration:.4f}s")
        # Expected: 0.5s (Notion) + 0.5s (Audio) + 0.5s (Image) = 1.5s (+ some overhead)

if __name__ == "__main__":
    unittest.main()
