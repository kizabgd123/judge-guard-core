import time
import os
import sqlite3
import shutil
from pathlib import Path
import sys

# Add current dir to path to import research_pipeline
sys.path.append(os.getcwd())
from research_pipeline import ResearchPipeline

def setup_test_env(num_files=100):
    research_dir = Path("bench_incremental")
    research_dir.mkdir(exist_ok=True)
    (research_dir / "phase1").mkdir(exist_ok=True)

    for i in range(num_files):
        with open(research_dir / "phase1" / f"test_{i}.md", "w") as f:
            f.write(f"# Test Document {i}\n\n")
            for j in range(20):
                f.write(f"### Pattern {j} - Description\n")
    return research_dir

def cleanup_test_env():
    if os.path.exists("bench_incremental"):
        shutil.rmtree("bench_incremental")
    if os.path.exists("bench_incremental.db"):
        os.remove("bench_incremental.db")

def benchmark():
    num_files = 100
    setup_test_env(num_files)

    import research_pipeline
    # Temporarily override config
    original_db_path = research_pipeline.DB_PATH
    original_research_dir = research_pipeline.RESEARCH_DIR
    research_pipeline.DB_PATH = Path("bench_incremental.db")
    research_pipeline.RESEARCH_DIR = Path("bench_incremental")

    try:
        pipeline = ResearchPipeline()
        pipeline.init_db()

        print(f"--- Baseline Benchmark (N={num_files} files, 2000 patterns) ---")

        # Initial Parse
        start_parse = time.time()
        pipeline.parse_markdown_files()
        end_parse = time.time()
        print(f"Initial parse_markdown_files: {end_parse - start_parse:.4f}s")

        # Initial Full Extraction
        start_extract = time.time()
        pipeline.extract_patterns()
        end_extract = time.time()
        full_extract_time = end_extract - start_extract
        print(f"Initial extract_patterns (Full Scan): {full_extract_time:.4f}s")

        # Simulate change in ONE file
        test_file = Path("bench_incremental/phase1/test_0.md")
        test_file.write_text("# Test Document 0 UPDATED\n\n### Pattern New - Description\n")

        # Incremental Parse (1 change)
        start_inc_parse = time.time()
        affected_ids = pipeline.parse_markdown_files()
        end_inc_parse = time.time()
        print(f"Incremental parse_markdown_files (1 change): {end_inc_parse - start_inc_parse:.4f}s")

        # Full Extraction (repeated for baseline)
        print("\nSimulating re-extraction of ONE change using FULL scan:")
        start_full_repeat = time.time()
        pipeline.extract_patterns()
        end_full_repeat = time.time()
        full_repeat_time = end_full_repeat - start_full_repeat
        print(f"Full extract_patterns: {full_repeat_time:.4f}s")

        # Incremental Extraction
        print("\nSimulating re-extraction of ONE change using INCREMENTAL scan (Optimized):")
        start_inc_extract = time.time()
        if affected_ids:
            pipeline.extract_patterns(doc_ids=affected_ids)
        end_inc_extract = time.time()
        inc_extract_time = end_inc_extract - start_inc_extract
        print(f"Incremental extract_patterns: {inc_extract_time:.4f}s")

        speedup = full_repeat_time / inc_extract_time if inc_extract_time > 0 else float('inf')
        print(f"\n⚡ Bolt Speedup: {speedup:.1f}x faster")

    finally:
        # Restore original config
        research_pipeline.DB_PATH = original_db_path
        research_pipeline.RESEARCH_DIR = original_research_dir
        cleanup_test_env()

if __name__ == "__main__":
    benchmark()
