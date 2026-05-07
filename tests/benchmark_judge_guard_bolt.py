import time
import os
import sys
import hashlib
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

def measure_import():
    start = time.time()
    if 'judge_guard' in sys.modules:
        del sys.modules['judge_guard']
    import judge_guard
    end = time.time()
    return end - start

def setup_db():
    # Ensure research.db exists for caching
    try:
        from research_pipeline import ResearchPipeline
        rp = ResearchPipeline().init_db()
        rp.close()
    except Exception:
        pass

def run_benchmark():
    setup_db()

    print("--- JudgeGuard Performance Benchmark (Baseline) ---")

    # 1. Measure Cold Import
    import_time = measure_import()
    print(f"Cold Import Time: {import_time*1000:.2f}ms")

    from judge_guard import JudgeGuard

    # Create WORK_LOG.md for testing if it doesn't exist
    if not os.path.exists("WORK_LOG.md"):
        with open("WORK_LOG.md", "w") as f:
            f.write("🟡 Starting baseline benchmark\n")
    else:
        # Append to ensure it's fresh enough for Layer 0
        with open("WORK_LOG.md", "a") as f:
            f.write("🟡 Starting baseline benchmark\n")

    # 2. Measure Initialization
    start = time.time()
    guard = JudgeGuard()
    init_time = time.time() - start
    print(f"Initialization Time: {init_time*1000:.2f}ms")

    action = "Baseline benchmark action"

    # Ensure it's cached for the "Warm" measurement
    # We mock gemini and block judge to avoid real API calls during baseline
    with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True),          patch('src.antigravity_core.gemini_client.GeminiClient.judge_content', return_value=True):
        guard.verify_action(action)

    # 3. Measure Cached Verification (Hot Path)
    start = time.time()
    guard.verify_action(action)
    cached_time = time.time() - start
    print(f"Cached Verification Latency: {cached_time*1000:.2f}ms")

    # 4. Measure Non-Cached Verification (excluding LLM latency)
    new_action = f"New action {time.time()}"
    with patch('src.antigravity_core.judge_flow.BlockJudge.evaluate', return_value=True):
        # We only measure the overhead before the judge call
        start = time.time()
        # To measure overhead we mock the evaluate but not the rest
        # Actually verify_action is complex, let's just see total
        guard.verify_action(new_action)
        non_cached_time = time.time() - start
        print(f"Non-Cached Verification (Mocked LLM): {non_cached_time*1000:.2f}ms")

if __name__ == "__main__":
    run_benchmark()
