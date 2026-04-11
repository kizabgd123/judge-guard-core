import time
import os
import sys
from unittest.mock import MagicMock, patch
import json

# Ensure project root is in path
sys.path.append(os.getcwd())

from research_pipeline import ResearchPipeline

def benchmark_sync_to_notion(iterations=5, queue_size=10):
    pipeline = ResearchPipeline()

    # Mock requests to simulate network latency
    mock_response = MagicMock()
    mock_response.status_code = 200

    def slow_post(*args, **kwargs):
        time.sleep(0.1)  # Simulate 100ms latency per call
        return mock_response

    with patch.object(pipeline.session, 'post', side_effect=slow_post) as mock_post, \
         patch('dotenv.load_dotenv'):

        # Pre-fill queue
        for i in range(queue_size):
            pipeline.notion_queue.append({
                "action": f"Action {i}",
                "details": "Details",
                "timestamp": "2026-01-01T00:00:00"
            })

        print(f"--- Benchmarking sync_to_notion ({queue_size} entries) ---")

        start_time = time.time()
        for _ in range(iterations):
            # Re-fill queue because sync_to_notion clears it
            pipeline.notion_queue = [{
                "action": f"Action {i}",
                "details": "Details",
                "timestamp": "2026-01-01T00:00:00"
            } for i in range(queue_size)]

            pipeline.sync_to_notion()

        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        print(f"Average time per sync: {avg_time:.4f}s")
        print(f"Total requests made: {mock_post.call_count}")

if __name__ == "__main__":
    # Mock environment variables
    os.environ["NOTION_TOKEN"] = "test_token"
    os.environ["NOTION_DATABASE_ID"] = "test_db"

    benchmark_sync_to_notion()
