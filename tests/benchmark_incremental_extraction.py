import time
import sqlite3
import os
import hashlib
from pathlib import Path
import sys

# Ensure current dir is in path
sys.path.append(os.getcwd())

from research_pipeline import ResearchPipeline, DB_PATH

def setup_mock_files(count=100):
    RESEARCH_DIR = Path("./research_mock")
    RESEARCH_DIR.mkdir(exist_ok=True)
    for i in range(count):
        phase_dir = RESEARCH_DIR / f"phase{i%3}"
        phase_dir.mkdir(exist_ok=True)
        file_path = phase_dir / f"file_{i}.md"
        file_path.write_text(f"# Title {i}\n\nContent for file {i}\n\n### Pattern {i} - HIGH\nDescription here.")
    return RESEARCH_DIR

def teardown_mock_files(path):
    import shutil
    if path.exists():
        shutil.rmtree(path)

class BenchmarkParsing:
    def __init__(self, db_path="benchmark_parse.db"):
        self.db_path = Path(db_path)
        if self.db_path.exists():
            os.remove(self.db_path)

    def run(self):
        count = 100
        mock_dir = setup_mock_files(count)

        # Patch RESEARCH_DIR in research_pipeline
        import research_pipeline
        original_dir = research_pipeline.RESEARCH_DIR
        research_pipeline.RESEARCH_DIR = mock_dir

        try:
            # 1. Initial Parse
            print(f"--- Benchmarking Initial Parse of {count} files ---")
            pipeline = ResearchPipeline()
            # Patch DB_PATH
            original_db_path = research_pipeline.DB_PATH
            research_pipeline.DB_PATH = self.db_path

            pipeline.init_db()

            start = time.time()
            affected_ids = pipeline.parse_markdown_files()
            duration = time.time() - start
            print(f"Initial parse duration: {duration:.4f}s (Affected: {len(affected_ids)})")

            # 2. Subsequent Parse (no changes)
            print(f"--- Benchmarking Subsequent Parse (0 changes) ---")
            start = time.time()
            affected_ids = pipeline.parse_markdown_files()
            duration = time.time() - start
            print(f"Subsequent parse (no changes) duration: {duration:.4f}s (Affected: {len(affected_ids)})")

            # 3. Subsequent Parse (1 change)
            print(f"--- Benchmarking Subsequent Parse (1 change) ---")
            (mock_dir / "phase0" / "file_0.md").write_text("# Title 0 UPDATED\n\nContent for file 0\n\n### Pattern 0 - HIGH")
            start = time.time()
            affected_ids = pipeline.parse_markdown_files()
            duration = time.time() - start
            print(f"Subsequent parse (1 change) duration: {duration:.4f}s (Affected: {len(affected_ids)})")

            # 4. Pattern Extraction (Full)
            print(f"--- Benchmarking Full Pattern Extraction ---")
            start = time.time()
            extracted = pipeline.extract_patterns()
            duration = time.time() - start
            print(f"Full pattern extraction duration: {duration:.4f}s (Extracted: {extracted})")

            # 5. Pattern Extraction (Incremental)
            print(f"--- Benchmarking Incremental Pattern Extraction ---")
            start = time.time()
            extracted = pipeline.extract_patterns(doc_ids=affected_ids)
            duration = time.time() - start
            print(f"Incremental pattern extraction duration: {duration:.4f}s (Extracted: {extracted})")

            pipeline.close()

        finally:
            research_pipeline.RESEARCH_DIR = original_dir
            research_pipeline.DB_PATH = original_db_path
            teardown_mock_files(mock_dir)
            if self.db_path.exists():
                os.remove(self.db_path)

if __name__ == "__main__":
    BenchmarkParsing().run()
