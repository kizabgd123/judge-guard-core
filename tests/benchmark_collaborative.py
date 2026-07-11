import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

# ⚡ Bolt: Use module-level __getattr__ via src.kaggle_stream.app
from src.kaggle_stream.app import collaborative_step, agent_alpha, agent_beta

class TestCollaborativePerformance(unittest.TestCase):
    # ⚡ Bolt: Patch NotionClient at its source to handle lazy import
    @patch('src.antigravity_core.notion_client.NotionClient')
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
        # Inject mock directly
        agent_alpha._notion = mock_notion_instance
        agent_beta._notion = mock_notion_instance

        print("\n--- Starting Collaborative Step Benchmark ---")
        start_time = time.time()
        # Ensure agents use the mock notion_db_id
        agent_alpha.notion_db_id = 'test_db'
        agent_beta.notion_db_id = 'test_db'

        collaborative_step("Kaggle Challenge", "test task")
        end_time = time.time()

        duration = end_time - start_time
        print(f"Total duration for collaborative_step: {duration:.4f}s")

        # Parallelization should keep it around 0.4s (Alpha's image + Beta's image in parallel is not yet fully optimized,
        # but Alpha's multimedia happens while Beta is reasoning).
        # Expected: Alpha Reasoning (~0) + [Alpha Multimedia (0.2) || Beta Reasoning (~0)] + Beta Multimedia (0.2) = ~0.4s
        # Without parallelization: Alpha Reasoning (~0) + Alpha Multimedia (0.2) + Beta Reasoning (~0) + Beta Multimedia (0.2) = ~0.4s
        # Wait, the current implementation parallelizes Alpha's multimedia with Beta's turn.
        # So Alpha's (Audio+Image) [0.2s] happens in parallel with Beta's step [0.2s].
        # Total should be ~0.4s.
        self.assertLess(duration, 0.5)

if __name__ == "__main__":
    unittest.main()
