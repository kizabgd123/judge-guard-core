import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.kaggle_stream.app import run_agent_turn
from src.kaggle_stream.kaggle_agent import KaggleAgent

class TestPerformance(unittest.TestCase):
    @patch('src.antigravity_core.notion_client.NotionClient')
    @patch('src.kaggle_stream.app.multimedia')
    def test_run_agent_turn_latency(self, mock_multimedia, mock_notion_class):
        # Setup Notion mock to avoid real API calls
        mock_notion_instance = MagicMock()
        mock_notion_class.return_value = mock_notion_instance

        # Setup Multimedia mock with artificial latency
        def slow_audio(*args, **kwargs):
            time.sleep(0.1)
            return "audio.mp3"
        def slow_image(*args, **kwargs):
            time.sleep(0.1)
            return "image.png"

        mock_multimedia.generate_audio.side_effect = slow_audio
        mock_multimedia.generate_mood_image.side_effect = slow_image

        agent = KaggleAgent(name="TestAgent")
        agent.demo_mode = True
        agent._notion = mock_notion_instance
        agent.notion_db_id = "test_db"

        print("\n--- Starting run_agent_turn Performance Test ---")

        # Test 1: Synchronous wait (default)
        start_sync = time.time()
        run_agent_turn(agent, "test task", return_futures=False)
        end_sync = time.time()
        sync_duration = end_sync - start_sync
        print(f"Synchronous duration: {sync_duration:.4f}s")

        # Test 2: Pipelined (returns futures)
        start_async = time.time()
        msg, img_fut, aud_fut, thought = run_agent_turn(agent, "test task", return_futures=True)
        # In a real app, we do other things here (like start next agent)
        # For test, we just wait for results
        img_fut.result()
        aud_fut.result()
        end_async = time.time()
        async_duration = end_async - start_async
        print(f"Pipelined duration: {async_duration:.4f}s")

        # Verify pipelining actually happens (should be ~0.1s total wait instead of 0.2s)
        # We allow some overhead, but it should be significantly less than sync (0.2s)
        self.assertLess(async_duration, sync_duration)
        self.assertLess(async_duration, 0.15)

if __name__ == "__main__":
    unittest.main()
