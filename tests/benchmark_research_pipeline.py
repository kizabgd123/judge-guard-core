import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure current dir is in path
sys.path.append(os.getcwd())

from research_pipeline import ResearchPipeline

class BenchmarkResearchPipeline(unittest.TestCase):
    def setUp(self):
        # Use a temporary DB for the benchmark
        self.db_path = "benchmark_research.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        with patch('research_pipeline.DB_PATH', self.db_path):
            self.pipeline = ResearchPipeline()
            self.pipeline.init_db()

    def tearDown(self):
        if hasattr(self.pipeline, 'conn') and self.pipeline.conn:
            self.pipeline.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if hasattr(self.pipeline, 'close'):
            self.pipeline.close()

    @patch('requests.Session.post')
    def test_sync_to_notion_latency(self, mock_post):
        # Setup mocks
        def slow_post(*args, **kwargs):
            time.sleep(0.1) # Simulate 100ms Notion API latency
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "Success"
            return mock_resp

        mock_post.side_effect = slow_post

        # Add 10 entries to the queue
        for i in range(10):
            self.pipeline.notion_queue.append({
                "action": f"Action {i}",
                "details": f"Details {i}",
                "timestamp": "2023-01-01T00:00:00"
            })

        # Set environment variables so sync_to_notion tries to use requests
        with patch.dict('os.environ', {'NOTION_TOKEN': 'secret', 'NOTION_DATABASE_ID': 'db_id'}):
            print(f"\n--- Starting ResearchPipeline Benchmark ({len(self.pipeline.notion_queue)} entries) ---")
            start_time = time.time()
            self.pipeline.sync_to_notion()
            end_time = time.time()

            duration = end_time - start_time
            print(f"Total duration: {duration:.4f}s")

            # For 10 entries, sequential should take ~1.0s
            # Parallel (5 workers) should take ~0.2s

if __name__ == "__main__":
    unittest.main()
