import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

class TestCollaborativePerformance(unittest.TestCase):
    @patch('src.antigravity_core.notion_client.NotionClient')
    @patch('src.kaggle_stream.app.multimedia')
    def test_collaborative_step_latency(self, mock_multimedia, mock_notion_class):
        # We must import inside the test or use patch on the module where it's used
        # because the module uses lazy loading.
        from src.kaggle_stream.app import collaborative_step, agent_alpha, agent_beta

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
        # Re-inject the mocked notion instance because KaggleAgent might have tried to init its own
        agent_alpha._notion = mock_notion_instance
        agent_beta._notion = mock_notion_instance

        print("\n--- Starting Collaborative Step Benchmark ---")
        start_time = time.time()
        with patch.dict('os.environ', {'NOTION_KAGGLE_DB_ID': 'test_db'}):
            collaborative_step("Kaggle Challenge", "test task")
        end_time = time.time()

        duration = end_time - start_time
        print(f"Total duration for collaborative_step: {duration:.4f}s")

        # Since we parallelized, it should be faster than sequential 0.2*4 + 0.1*2 = 1.0s
        # Actually Alpha starts, returns futures.
        # Beta starts, returns results (0.2s for Beta multimedia, but that's in background)
        # Alpha results are awaited.
        # In current implementation:
        # run_agent_turn(alpha) -> reasoning (fast) + submit(audio, image) -> return futures
        # run_agent_turn(beta) -> reasoning (fast) + submit(audio, image) -> result() (waits 0.2s)
        # wait for alpha's result (already finished or near finishing)
        # Total should be around 0.2s + overhead.
        self.assertGreaterEqual(duration, 0.2) # Should take at least 0.2s now due to mocking working
        self.assertLess(duration, 0.8)

if __name__ == "__main__":
    unittest.main()
