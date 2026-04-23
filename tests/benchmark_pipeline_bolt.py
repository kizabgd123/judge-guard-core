import time
import os
import shutil
import sqlite3
from pathlib import Path
import sys
import logging

# Add src to path
sys.path.append(os.getcwd())

from research_pipeline import ResearchPipeline

# Disable logging for benchmark
logging.getLogger("research_pipeline").setLevel(logging.WARNING)

BENCH_DIR = Path("./bench_research")
BENCH_DB = Path("./bench_research.db")

def setup_bench(count=500, size_kb=100):
    if BENCH_DIR.exists():
        shutil.rmtree(BENCH_DIR)
    BENCH_DIR.mkdir()

    dummy_content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * (size_kb * 2)

    for i in range(count):
        phase_dir = BENCH_DIR / f"phase{i % 3}"
        phase_dir.mkdir(exist_ok=True)
        md_file = phase_dir / f"test_{i}.md"
        content = f"# Test Document {i}\n\n"
        content += "### 🔥 High Priority Pattern\n"
        content += "### 🟢 Low Priority Pattern\n"
        content += "### Standard Pattern\n"
        content += dummy_content + "\n"
        md_file.write_text(content)

def run_benchmark():
    setup_bench(500, 100) # 500 files, ~100KB each

    # Mock RESEARCH_DIR and DB_PATH in research_pipeline
    import research_pipeline
    original_dir = research_pipeline.RESEARCH_DIR
    original_db = research_pipeline.DB_PATH
    research_pipeline.RESEARCH_DIR = BENCH_DIR
    research_pipeline.DB_PATH = BENCH_DB

    if BENCH_DB.exists():
        BENCH_DB.unlink()

    pipeline = ResearchPipeline()
    pipeline.init_db()

    print(f"--- Benchmarking ResearchPipeline with 500 files (~100KB each) ---")

    # First Run (Parsing)
    start = time.time()
    affected_ids = pipeline.parse_markdown_files()
    parse_time_1 = time.time() - start
    print(f"First run parse time: {parse_time_1:.4f}s")

    # First Run (Extraction)
    start = time.time()
    pipeline.extract_patterns(doc_ids=affected_ids)
    extract_time_1 = time.time() - start
    print(f"First run extraction time: {extract_time_1:.4f}s")

    # No-Change Run (Parsing)
    start = time.time()
    affected_ids_2 = pipeline.parse_markdown_files()
    parse_time_2 = time.time() - start
    print(f"No-change parse time: {parse_time_2:.4f}s")

    # Cleanup
    pipeline.close()
    if BENCH_DB.exists():
        BENCH_DB.unlink()
    shutil.rmtree(BENCH_DIR)

    # Restore original paths
    research_pipeline.RESEARCH_DIR = original_dir
    research_pipeline.DB_PATH = original_db

if __name__ == "__main__":
    run_benchmark()
