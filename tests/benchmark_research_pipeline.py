import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from research_pipeline import ResearchPipeline

class BenchmarkResearchPipeline(unittest.TestCase):
    def test_sync_to_notion_latency(self):
        pipeline = ResearchPipeline()
        for i in range(10):
            pipeline.log_audit(f"Action {i}", f"Details {i}")

        # Setup mock with artificial delay on the pipeline's session
        def slow_post(*args, **kwargs):
            time.sleep(0.1)  # 100ms latency
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            return mock_resp

        with patch.object(pipeline.session, 'post', side_effect=slow_post) as mock_post:
            # Ensure credentials exist to trigger API path
            with patch.dict('os.environ', {
                'NOTION_TOKEN': 'secret_token',
                'NOTION_DATABASE_ID': 'db_id'
            }):
                print(f"\n--- Starting ResearchPipeline Sync Benchmark (10 entries) ---")
                start_time = time.time()
                pipeline.sync_to_notion()
                end_time = time.time()

                duration = end_time - start_time
                print(f"Total duration: {duration:.4f}s")
                # Optimized expected: ~0.2s (10 * 0.1s / 5 workers) + overhead

if __name__ == "__main__":
    unittest.main()
