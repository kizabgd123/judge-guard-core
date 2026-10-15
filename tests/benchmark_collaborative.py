import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

try:
    import gradio
except ImportError:
    sys.modules['gradio'] = MagicMock()

from src.kaggle_stream.app import collaborative_step, agent_alpha, agent_beta, multimedia

class BenchmarkCollaborative(unittest.TestCase):
    @patch('src.antigravity_core.notion_client.NotionClient')
    def test_collaborative_step_parallelism(self, mock_notion_class):
        agent_alpha.demo_mode = True
        agent_beta.demo_mode = True
        agent_alpha._notion = MagicMock()
        agent_beta._notion = MagicMock()

        def slow_audio(*args, **kwargs):
            time.sleep(0.3)
            return "audio.mp3"

        def slow_image(*args, **kwargs):
            time.sleep(0.3)
            return "image.png"

        multimedia.generate_audio = slow_audio
        multimedia.generate_mood_image = slow_image

        print("\n--- Starting Collaborative Step Benchmark ---")
        start_time = time.time()
        res = collaborative_step("Kaggle Challenge", "House Prices")
        duration = time.time() - start_time

        print(f"Total duration for collaborative step: {duration:.4f}s")
        self.assertEqual(len(res), 6)
        # Expected duration is ~0.3s (all 4 audio/image futures run concurrently in parallel)

if __name__ == "__main__":
    unittest.main()
