import time
import os
import hashlib
import sqlite3
from pathlib import Path
from research_pipeline import ResearchPipeline, DB_PATH, RESEARCH_DIR

# Setup dummy research files
BENCH_DIR = Path("./research_bench")
BENCH_DIR.mkdir(exist_ok=True)

def setup_files(count=500, size_kb=10):
    for i in range(count):
        content = f"# Title {i}\n"
        content += "### 🔥 Critical Pattern - Something important\n"
        content += "### 🟢 Low Pattern - Something minor\n"
        content += "## 3. Regular Pattern - No icon\n"
        content += ("This is some dummy content for the benchmark. " * 20 * size_kb)
        (BENCH_DIR / f"test_{i}.md").write_text(content)

def clear_files():
    for f in BENCH_DIR.glob("**/*.md"):
        f.unlink()
    for d in reversed(list(BENCH_DIR.glob("**/*"))):
        if d.is_dir(): d.rmdir()
    if BENCH_DIR.exists(): BENCH_DIR.rmdir()

def benchmark():
    # Override RESEARCH_DIR
    import research_pipeline
    original_dir = research_pipeline.RESEARCH_DIR
    research_pipeline.RESEARCH_DIR = BENCH_DIR

    db_file = Path("bench_bolt.db")
    if db_file.exists(): db_file.unlink()

    # 1. Benchmark Initial Parse
    setup_files(500, 5) # 500 files, ~5KB each
    pipeline = ResearchPipeline()
    research_pipeline.DB_PATH = db_file
    pipeline.init_db()

    print(f"--- Benchmarking ResearchPipeline (500 files) ---")

    start = time.time()
    affected_ids = pipeline.parse_markdown_files()
    initial_parse_time = time.time() - start
    print(f"Initial parse: {initial_parse_time:.4f}s")

    # 2. Benchmark No-change Parse
    start = time.time()
    pipeline.parse_markdown_files()
    no_change_parse_time = time.time() - start
    print(f"No-change parse: {no_change_parse_time:.4f}s")

    # 3. Benchmark Pattern Extraction
    start = time.time()
    pipeline.extract_patterns(doc_ids=affected_ids)
    extraction_time = time.time() - start
    print(f"Pattern extraction: {extraction_time:.4f}s")

    pipeline.close()
    if db_file.exists(): db_file.unlink()
    research_pipeline.RESEARCH_DIR = original_dir
    clear_files()

    return initial_parse_time, no_change_parse_time, extraction_time

if __name__ == "__main__":
    benchmark()
