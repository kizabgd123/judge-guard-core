import time
import os
import sys

# Ensure we can import research_pipeline
sys.path.append(os.getcwd())

from unittest.mock import patch, MagicMock
from research_pipeline import ResearchPipeline

def benchmark_sync():
    pipeline = ResearchPipeline()
    # Add 10 entries to the queue
    pipeline.notion_queue = [
        {
            "action": f"Action {i}",
            "details": f"Details {i}",
            "timestamp": "2023-01-01T00:00:00"
        }
        for i in range(10)
    ]

    # Mock environment variables
    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda k, d=None: "mock_val" if k in ["NOTION_TOKEN", "NOTION_DATABASE_ID"] else d

        # Mock pipeline.session.post to simulate 100ms latency
        # ⚡ Bolt: Patch the session's post method to ensure the benchmark measures parallel execution
        with patch.object(pipeline.session, 'post') as mock_post:
            def slow_post(*args, **kwargs):
                time.sleep(0.1)
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                return mock_resp
            mock_post.side_effect = slow_post

            print("🚀 Starting benchmark (Parallel Sync)...")
            start_time = time.time()
            pipeline.sync_to_notion()
            end_time = time.time()

            duration = end_time - start_time
            print(f"✅ Parallel sync of 10 entries took: {duration:.4f} seconds")
            return duration

if __name__ == "__main__":
    benchmark_sync()
