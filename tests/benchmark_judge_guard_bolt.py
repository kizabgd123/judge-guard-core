import time
import os
import sys
import shutil
import tempfile
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock heavy dependencies that are not the subject of this benchmark
sys.modules['src.antigravity_core.gemini_client'] = MagicMock()
sys.modules['src.antigravity_core.mobile_bridge'] = MagicMock()

def run_benchmark():
    # Use a temporary directory for all file operations to avoid touching user's home dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Define paths within temp dir
        mock_home = os.path.join(tmp_dir, "home")
        mock_brain_base = os.path.join(mock_home, ".gemini/antigravity/brain")
        mock_rules_path = os.path.join(mock_home, ".gemini/MASTER_ORCHESTRATION.md")
        mock_work_log = os.path.join(tmp_dir, "WORK_LOG.md")
        mock_db_path = os.path.join(tmp_dir, "research.db")

        os.makedirs(mock_brain_base, exist_ok=True)
        os.makedirs(os.path.dirname(mock_rules_path), exist_ok=True)

        # Setup dummy brain folders
        for i in range(10):
            folder = os.path.join(mock_brain_base, f"2026-04-0{i}-120000")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "dummy"), "w") as f:
                f.write("dummy")

        # Setup rules file
        with open(mock_rules_path, "w") as f:
            f.write("# Rules\n" * 100) # 100 lines of rules

        # Setup WORK_LOG.md
        with open(mock_work_log, "w") as f:
            f.write("🟡 Starting Benchmark\n")

        # Mock environment and paths
        with patch('os.path.expanduser', side_effect=lambda p: p.replace("~", mock_home)), \
             patch.dict('os.environ', {
                 'BRAIN_PATH': '',
                 'WORK_LOG_PATH': mock_work_log
             }), \
             patch('research_pipeline.DB_PATH', mock_db_path):

            # Import judge_guard AFTER mocking
            if 'judge_guard' in sys.modules:
                del sys.modules['judge_guard']
            import judge_guard
            from research_pipeline import ResearchPipeline

            # Setup ResearchPipeline with a cached verdict
            pipeline = ResearchPipeline().init_db()
            pipeline.cache_verdict("Benchmarked Action", "PASSED")
            pipeline.close()

            print("\n--- ⚡ Bolt: JudgeGuard Performance Benchmark ---")

            # Measure Init (Hot loop)
            start = time.time()
            iterations = 1000
            for _ in range(iterations):
                g = judge_guard.JudgeGuard()
            end = time.time()
            avg_init_ms = (end - start) / iterations * 1000
            print(f"Average Init time: {avg_init_ms:.4f}ms")

            # Measure verify_action (Cache Hit)
            g = judge_guard.JudgeGuard()
            start = time.time()
            for _ in range(iterations):
                g.verify_action("Benchmarked Action")
            end = time.time()
            avg_verify_ms = (end - start) / iterations * 1000
            print(f"Average verify_action (Cache Hit): {avg_verify_ms:.4f}ms")

            # Safety checks
            assert avg_init_ms < 0.1, f"Init is too slow: {avg_init_ms:.4f}ms"
            assert avg_verify_ms < 0.3, f"Verify is too slow: {avg_verify_ms:.4f}ms"
            print("✅ Performance requirements met.")

if __name__ == "__main__":
    try:
        run_benchmark()
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        sys.exit(1)
