import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Ensure src is in path
sys.path.append(os.getcwd())

import src.kaggle_stream.app as app

class TestCollaborativePerformance(unittest.TestCase):
    @patch('src.antigravity_core.notion_client.NotionClient')
    def test_collaborative_step_latency(self, mock_notion_class):
        # Setup Notion mock to avoid real API calls and simulate latency
        mock_notion_instance = MagicMock()
        mock_notion_class.return_value = mock_notion_instance

        def slow_notion(*args, **kwargs):
            time.sleep(0.1)
            return {"id": "page_id"}
        mock_notion_instance.append_to_database.side_effect = slow_notion

        # Setup Multimedia mock to simulate latency
        mock_multimedia = MagicMock()
        def slow_audio(*args, **kwargs):
            time.sleep(0.2)
            return "audio.mp3"
        def slow_image(*args, **kwargs):
            time.sleep(0.2)
            return "image.png"

        mock_multimedia.generate_audio.side_effect = slow_audio
        mock_multimedia.generate_mood_image.side_effect = slow_image

        # Real executor for parallelism
        real_executor = ThreadPoolExecutor(max_workers=4)

        # Patch app resources
        with patch.object(app, 'multimedia', mock_multimedia), \
             patch.object(app, 'executor', real_executor), \
             patch.object(app, 'agent_alpha', app.agent_alpha), \
             patch.object(app, 'agent_beta', app.agent_beta):

            # Configure agents for demo mode to avoid Gemini API calls
            app.agent_alpha.demo_mode = True
            app.agent_beta.demo_mode = True
            app.agent_alpha._notion = mock_notion_instance
            app.agent_beta._notion = mock_notion_instance

            print("\n--- Starting Collaborative Step Benchmark ---")
            start_time = time.time()
            with patch.dict('os.environ', {'NOTION_KAGGLE_DB_ID': 'test_db'}):
                app.collaborative_step("Kaggle Challenge", "test task")
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration for collaborative_step: {duration:.4f}s")
            real_executor.shutdown()

if __name__ == "__main__":
    unittest.main()
