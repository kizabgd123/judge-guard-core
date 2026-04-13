import time
import os
import json
import unittest
from unittest.mock import patch, MagicMock
from research_pipeline import ResearchPipeline

class MockResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

def mock_post(*args, **kwargs):
    time.sleep(0.1)  # Simulate 100ms latency
    return MockResponse(200, "OK")

class BenchmarkResearchPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = ResearchPipeline()
        # Mock env vars
        os.environ["NOTION_TOKEN"] = "fake_token"
        os.environ["NOTION_DATABASE_ID"] = "fake_db_id"

        # Fill queue with 10 entries
        for i in range(10):
            self.pipeline.notion_queue.append({
                "action": f"Action {i}",
                "details": f"Details {i}",
                "timestamp": "2023-01-01T00:00:00"
            })

    def tearDown(self):
        self.pipeline.close()

    @patch("requests.Session.post", side_effect=mock_post)
    def test_sync_performance_parallel(self, mock_post_func):
        # The new implementation uses self.session.post
        start_time = time.time()
        self.pipeline.sync_to_notion()
        end_time = time.time()

        duration = end_time - start_time
        print(f"\nParallel sync duration (10 entries): {duration:.4f}s")
        # Expected duration: ~0.2s (since max_workers=5 and we have 10 entries, 2 batches of 0.1s)

    def test_sync_performance_sequential_manual(self):
        # Manual sequential run for comparison
        import requests
        headers = {"Authorization": "Bearer fake", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}

        start_time = time.time()
        with patch("requests.post", side_effect=mock_post):
            for entry in self.pipeline.notion_queue:
                requests.post("http://fake", headers=headers, json={})
        end_time = time.time()

        duration = end_time - start_time
        print(f"Sequential sync duration (10 entries): {duration:.4f}s")

if __name__ == "__main__":
    unittest.main()
