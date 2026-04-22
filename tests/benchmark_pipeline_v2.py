import time
import os
import shutil
import hashlib
from pathlib import Path
from research_pipeline import ResearchPipeline

# Configuration
BENCHMARK_DIR = Path("./benchmark_research_v2")
DB_PATH = Path("./benchmark_research_v2.db")
NUM_FILES = 1000

def setup_files():
    if BENCHMARK_DIR.exists():
        shutil.rmtree(BENCHMARK_DIR)
    BENCHMARK_DIR.mkdir(parents=True)

    for i in range(NUM_FILES):
        file_path = BENCHMARK_DIR / f"file_{i}.md"
        content = f"# Title {i}\nThis is content for file {i}."
        file_path.write_text(content, encoding="utf-8")

def run_benchmark():
    if DB_PATH.exists():
        os.remove(DB_PATH)

    # Global overrides for research_pipeline
    import research_pipeline
    original_dir = research_pipeline.RESEARCH_DIR
    original_db = research_pipeline.DB_PATH
    research_pipeline.RESEARCH_DIR = BENCHMARK_DIR
    research_pipeline.DB_PATH = DB_PATH

    pipeline = ResearchPipeline()
    pipeline.init_db()

    # Initial parse (cold start)
    print(f"--- Cold Parse of {NUM_FILES} files ---")
    start = time.time()
    pipeline.parse_markdown_files()
    end = time.time()
    print(f"Cold parse time: {end - start:.4f}s")

    # Second parse (no changes)
    print(f"\n--- Hot Parse (No Changes) of {NUM_FILES} files ---")
    start = time.time()
    pipeline.parse_markdown_files()
    end = time.time()
    print(f"Hot parse time: {end - start:.4f}s")

    # Cleanup
    pipeline.close()
    research_pipeline.RESEARCH_DIR = original_dir
    research_pipeline.DB_PATH = original_db
    if DB_PATH.exists():
        os.remove(DB_PATH)
    if BENCHMARK_DIR.exists():
        shutil.rmtree(BENCHMARK_DIR)

if __name__ == "__main__":
    setup_files()
    try:
        run_benchmark()
    finally:
        if BENCHMARK_DIR.exists():
            shutil.rmtree(BENCHMARK_DIR)
