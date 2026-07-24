import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.kaggle_stream.app import collaborative_step, agent_alpha, agent_beta

class TestCollaborativePerformance(unittest.TestCase):
    @patch('src.kaggle_stream.kaggle_agent.NotionClient')
    @patch('src.kaggle_stream.app.multimedia')
    def test_collaborative_step_latency(self, mock_multimedia, mock_notion_class):
        # Setup Notion mock to avoid real API calls and simulate latency
        mock_notion_instance = MagicMock()
        mock_notion_class.return_value = mock_notion_instance

        def slow_notion(*args, **kwargs):
            time.sleep(0.1) # Reduced from 0.5 to keep test reasonably fast
            return {"id": "page_id"}
        mock_notion_instance.append_to_database.side_effect = slow_notion

        # Setup Multimedia mock to simulate latency
        def slow_audio(*args, **kwargs):
            time.sleep(0.2)
            return "audio.mp3"
        def slow_image(*args, **kwargs):
            time.sleep(0.2)
            return "image.png"

        mock_multimedia.generate_audio.side_effect = slow_audio
        mock_multimedia.generate_mood_image.side_effect = slow_image

        # Configure agents for demo mode to avoid Gemini API calls
        agent_alpha.demo_mode = True
        agent_beta.demo_mode = True
        agent_alpha.notion = mock_notion_instance
        agent_beta.notion = mock_notion_instance

        print("\n--- Starting Collaborative Step Benchmark ---")
        start_time = time.time()
        with patch.dict('os.environ', {'NOTION_KAGGLE_DB_ID': 'test_db'}):
            collaborative_step("Kaggle Challenge", "test task")
        end_time = time.time()

        duration = end_time - start_time
        print(f"Total duration for collaborative_step: {duration:.4f}s")

if __name__ == "__main__":
    unittest.main()
