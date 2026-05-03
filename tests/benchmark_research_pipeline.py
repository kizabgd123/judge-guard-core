import time
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.getcwd())

from research_pipeline import ResearchPipeline

def setup_test_files(count=100):
    temp_dir = tempfile.mkdtemp()
    research_dir = Path(temp_dir) / "research"
    research_dir.mkdir()

    for i in range(count):
        phase_dir = research_dir / f"phase_{i % 5}"
        phase_dir.mkdir(exist_ok=True)
        with open(phase_dir / f"test_doc_{i}.md", "w") as f:
            f.write(f"# Test Document {i}\n\n")
            f.write(f"This is test document number {i}.\n")
            f.write(f"### Pattern {i} - High priority\n")
            f.write("Some description here.\n")

    return temp_dir

def run_benchmark():
    print("--- ResearchPipeline Performance Baseline ---")

    temp_dir = setup_test_files(100)
    db_path = Path(temp_dir) / "test_research.db"
    research_dir = Path(temp_dir) / "research"

    # Patch constants in research_pipeline
    import research_pipeline
    original_db_path = research_pipeline.DB_PATH
    original_research_dir = research_pipeline.RESEARCH_DIR
    research_pipeline.DB_PATH = db_path
    research_pipeline.RESEARCH_DIR = research_dir

    try:
        pipeline = ResearchPipeline().init_db()

        # 1. Bulk Parse Baseline
        start = time.time()
        affected_ids = pipeline.parse_markdown_files()
        end = time.time()
        parse_time = end - start
        print(f"Bulk Parse (100 files): {parse_time:.4f}s")

        # 2. Pattern Extraction Baseline
        start = time.time()
        patterns = pipeline.extract_patterns(doc_ids=affected_ids)
        end = time.time()
        extract_time = end - start
        print(f"Pattern Extraction (100 files): {extract_time:.4f}s")

        # 3. Warm Parse (no changes)
        start = time.time()
        pipeline.parse_markdown_files()
        end = time.time()
        warm_parse_time = end - start
        print(f"Warm Parse (no changes): {warm_parse_time:.4f}s")

    finally:
        research_pipeline.DB_PATH = original_db_path
        research_pipeline.RESEARCH_DIR = original_research_dir
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_benchmark()
